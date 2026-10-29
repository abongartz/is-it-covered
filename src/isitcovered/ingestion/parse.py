"""Structural parser: PDF -> section tree (headings, text blocks, pages, coordinates).

Rule-based on top of PyMuPDF. Text lines sharing a baseline are merged into rows; repeated page headers and
page numbers are dropped; headings are recognised from their numbering and typography by a layout profile,
one per insurer layout. Offline only: PyMuPDF is not installed on the app host.
"""

import re
import unicodedata
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

from isitcovered.models.sections import BBox, BlockKind, Section, SectionKind, SectionTree, TextBlock

PARSER_VERSION = "1"

HEADER_ZONE = 0.10  # top fraction of the page where running headers live
FOOTER_ZONE = 0.92  # rows starting below this fraction are page numbers or footnotes
HEADER_MIN_PAGE_SHARE = 0.3  # a top row repeated on this share of pages is a running header
ROW_Y_TOLERANCE = 3.0
PARAGRAPH_GAP = 13.0  # baseline gap (pt) above which a new block starts (line spacing is ~11 pt at 9 pt)
WHITE = 0xFFFFFF

BULLET_RE = re.compile(r"^(•|–|-|[a-z]\)|\d+°)\s")
_SPACES_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Collapse every kind of whitespace (tabs, thin and non-breaking spaces) to a single space."""
    return _SPACES_RE.sub(" ", text.replace("­", "")).strip()


def round_bbox(bbox: BBox) -> BBox:
    return tuple(round(v, 1) for v in bbox)  # type: ignore[return-value]


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


@dataclass
class Span:
    text: str
    font: str
    size: float
    color: int
    flags: int
    bbox: BBox
    baseline: float

    @property
    def bold(self) -> bool:
        return "Bold" in self.font or "Black" in self.font or bool(self.flags & 16)

    @property
    def italic(self) -> bool:
        return "Ita" in self.font or "Oblique" in self.font or bool(self.flags & 2)


@dataclass
class Row:
    """PDF lines of one page sharing a baseline, sorted left to right (e.g. a number and its title)."""

    page: int
    lines: list[list[Span]]

    @property
    def spans(self) -> list[Span]:
        return [span for line in self.lines for span in line]

    @property
    def text(self) -> str:
        # Spans of one line are contiguous; separate lines on the same baseline are separate words.
        return normalize(" ".join("".join(s.text for s in line) for line in self.lines))

    @property
    def bbox(self) -> BBox:
        return (
            min(s.bbox[0] for s in self.spans),
            min(s.bbox[1] for s in self.spans),
            max(s.bbox[2] for s in self.spans),
            max(s.bbox[3] for s in self.spans),
        )

    @property
    def lead(self) -> Span:
        """First span carrying text, skipping bullet glyphs."""
        for span in self.spans:
            if span.text.strip() and span.text.strip() != "•":
                return span
        return self.spans[0]

    @property
    def baseline(self) -> float:
        return max(s.baseline for s in self.spans)

    @property
    def bold(self) -> bool:
        return all(s.bold for s in self.spans if s.text.strip() and s.text.strip() != "•")


@dataclass
class Heading:
    kind: SectionKind
    title: str
    number: str | None = None


@dataclass
class ParseContext:
    in_lexicon: bool
    in_toc: bool


Classifier = Callable[[Row, ParseContext], Heading | None]


@dataclass(frozen=True)
class LayoutProfile:
    name: str
    classify: Classifier
    cover_pages: tuple[int, ...] = (1,)
    back_cover_pages: tuple[int, ...] = ()  # negative numbers count from the end
    toc_title: str = "Table des matières"
    lexicon_title: str = "Lexique"


def _classify_ethias(row: Row, ctx: ParseContext) -> Heading | None:
    lead, text = row.lead, row.text
    if not lead.bold or (ctx.in_toc and lead.size < 13.5):  # TOC entries are bold too
        return None
    if lead.size >= 13.5:
        if m := re.match(r"^Chapitre\s+([IVXLC]+)\b\s*(.*)$", text):
            return Heading("chapter", m[2], m[1])
        return Heading("front", text)
    if 9.5 <= lead.size <= 10.5:
        if lead.color == WHITE and (m := re.match(r"^Article\s+(\d+)\s*(.*)$", text)):
            return Heading("article", m[2], m[1])
        if row.bbox[0] < 100 and (m := re.match(r"^(\d+(?:\.\d+)+)\.?\s+(.+)$", text)):
            return Heading("subarticle", m[2], m[1])
        if lead.color != WHITE:
            return Heading("heading", text)
    if 8.5 <= lead.size <= 9.5 and row.bold and row.bbox[0] < 120:
        if ctx.in_lexicon:
            return Heading("term", text)
        if m := re.match(r"^([A-Z])\.\s+(.+)$", text):
            return Heading("heading", m[2], m[1])
    return None


PROFILES: dict[str, LayoutProfile] = {
    "ethias-2025": LayoutProfile(name="ethias-2025", classify=_classify_ethias, back_cover_pages=(-1,)),
}
DEFAULT_PROFILE_BY_INSURER = {"Ethias": "ethias-2025"}


# --- Rows -------------------------------------------------------------------------------------------------


def extract_rows(doc: pymupdf.Document) -> list[list[Row]]:
    """Rows of every page (index 0 = page 1), in reading order."""
    pages: list[list[Row]] = []
    for page in doc:
        lines = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = [
                    Span(
                        s["text"],
                        s["font"],
                        s["size"],
                        s["color"],
                        s["flags"],
                        tuple(s["bbox"]),
                        s["origin"][1],
                    )
                    for s in line["spans"]
                ]
                if any(s.text.strip() for s in spans):
                    lines.append(spans)
        lines.sort(key=lambda spans: (max(s.baseline for s in spans), spans[0].bbox[0]))
        rows: list[Row] = []
        for spans in lines:
            baseline = max(s.baseline for s in spans)
            if rows and abs(rows[-1].baseline - baseline) <= ROW_Y_TOLERANCE:
                rows[-1].lines.append(spans)
                rows[-1].lines.sort(key=lambda line: line[0].bbox[0])
            else:
                rows.append(Row(page.number + 1, [spans]))
        pages.append(rows)
    return pages


def strip_page_furniture(pages: list[list[Row]], page_height: float) -> list[list[Row]]:
    """Drop running headers (top rows repeated across pages) and page numbers."""
    top_texts = Counter(
        row.text
        for rows in pages
        for row in {r.text: r for r in rows if r.bbox[3] < HEADER_ZONE * page_height}.values()
    )
    headers = {t for t, n in top_texts.items() if n >= max(2, HEADER_MIN_PAGE_SHARE * len(pages))}
    return [
        [
            row
            for row in rows
            if not (row.bbox[3] < HEADER_ZONE * page_height and row.text in headers)
            and not (row.bbox[1] > FOOTER_ZONE * page_height and row.text.isdigit())
        ]
        for rows in pages
    ]


# --- Tree -------------------------------------------------------------------------------------------------


@dataclass
class _Node:
    section: Section
    rows: list[Row] = field(default_factory=list)  # body rows, turned into blocks at the end
    title_rows: list[Row] = field(default_factory=list)  # heading rows (a title may wrap)


class _TreeBuilder:
    LEVELS = {"front": 1, "chapter": 1, "article": 2}

    def __init__(self) -> None:
        self.roots: list[Section] = []
        self.stack: list[_Node] = []
        self.ids: Counter[str] = Counter()
        self.nodes: list[_Node] = []

    @property
    def current(self) -> _Node | None:
        return self.stack[-1] if self.stack else None

    def open(self, heading: Heading, row: Row) -> _Node:
        kind = heading.kind
        if kind in self.LEVELS:
            level = self.LEVELS[kind]
            self._pop_to(level)
        elif kind == "subarticle":
            level = heading.number.count(".") + 2
            self._pop_to(level)
        elif kind == "term":
            while self.stack and self.stack[-1].section.kind != "chapter":
                self.stack.pop()
            level = 2
        else:  # unnumbered heading: child of the deepest numbered section
            while self.stack and self.stack[-1].section.kind == "heading":
                self.stack.pop()
            level = self.stack[-1].section.level + 1 if self.stack else 1

        parent = self.current
        section = Section(
            id=self._make_id(heading, parent),
            kind=kind,
            number=heading.number,
            title=heading.title,
            level=level,
            page_start=row.page,
            page_end=row.page,
            bbox=round_bbox(row.bbox),
        )
        node = _Node(section, title_rows=[row])
        (parent.section.children if parent else self.roots).append(section)
        self.stack.append(node)
        self.nodes.append(node)
        return node

    def _pop_to(self, level: int) -> None:
        while self.stack and self.stack[-1].section.level >= level:
            self.stack.pop()

    def _make_id(self, heading: Heading, parent: _Node | None) -> str:
        match heading.kind:
            case "chapter":
                base = f"ch-{heading.number.lower()}"
            case "article" | "subarticle":
                base = f"art-{heading.number}"
            case "term":
                base = f"def-{slugify(heading.title)}"
            case "heading" if heading.number:
                base = f"{parent.section.id}/{heading.number}" if parent else heading.number
            case "heading":
                rank = 1 + (sum(1 for c in parent.section.children if c.kind == "heading") if parent else 0)
                base = f"{parent.section.id}/h{rank}" if parent else f"h{rank}"
            case _:
                base = slugify(heading.title) or "front"
        self.ids[base] += 1
        return base if self.ids[base] == 1 else f"{base}-{self.ids[base]}"


def _italic_runs(rows: list[Row]) -> list[str]:
    """Consecutive italic text, spanning line breaks (whitespace-only spans do not interrupt a run)."""
    runs: list[str] = []
    current = ""
    for row in rows:
        for line in row.lines:
            for span in line:
                if span.italic or (current and not span.text.strip()):
                    current += span.text
                elif current:
                    runs.append(normalize(current))
                    current = ""
            current += " " if current else ""
    if current.strip():
        runs.append(normalize(current))
    return [r for r in runs if r]


def _make_blocks(rows: list[Row], page_height: float) -> list[TextBlock]:
    groups: list[list[Row]] = []
    for row in rows:
        prev = groups[-1][-1] if groups else None
        starts_new = (
            prev is None
            or row.page != prev.page
            or BULLET_RE.match(row.text) is not None
            or row.bold != prev.bold
            or row.baseline - prev.baseline > PARAGRAPH_GAP
            or row.bbox[0] < groups[-1][0].bbox[0] - 5
            or _is_footnote(row, page_height) != _is_footnote(prev, page_height)
        )
        if starts_new:
            groups.append([row])
        else:
            groups[-1].append(row)

    blocks = []
    for group in groups:
        first = group[0]
        kind: BlockKind
        if _is_footnote(first, page_height):
            kind = "footnote"
        elif BULLET_RE.match(first.text):
            kind = "list_item"
        elif first.bold:
            kind = "label"
        else:
            kind = "paragraph"
        boxes = [r.bbox for r in group]
        bbox = (
            min(b[0] for b in boxes),
            min(b[1] for b in boxes),
            max(b[2] for b in boxes),
            max(b[3] for b in boxes),
        )
        text = normalize(" ".join(r.text for r in group))
        blocks.append(
            TextBlock(
                kind=kind, text=text, page=first.page, bbox=round_bbox(bbox), italic=_italic_runs(group)
            )
        )
    return blocks


def _is_footnote(row: Row, page_height: float) -> bool:
    return row.bbox[1] > FOOTER_ZONE * page_height and row.text.startswith("*")


def build_tree(pages: list[list[Row]], profile: LayoutProfile, page_height: float) -> list[Section]:
    builder = _TreeBuilder()
    page_count = len(pages)
    back_cover = {p if p > 0 else page_count + 1 + p for p in profile.back_cover_pages}
    pending_title: _Node | None = None  # heading whose title may continue on the next row

    for rows in pages:
        for row in rows:
            if row.page in back_cover and (
                builder.current is None or builder.current.section.title != "Quatrième de couverture"
            ):
                builder.stack.clear()
                builder.open(Heading("front", "Quatrième de couverture"), row)
            elif builder.current is None and row.page in profile.cover_pages:
                builder.open(Heading("front", "Couverture"), row)

            current = builder.current
            ctx = ParseContext(
                in_lexicon=any(
                    n.section.kind == "chapter" and n.section.title == profile.lexicon_title
                    for n in builder.stack
                ),
                in_toc=current is not None and current.section.title == profile.toc_title,
            )
            special_page = row.page in back_cover or row.page in profile.cover_pages
            heading = None if special_page else profile.classify(row, ctx)

            if pending_title and _continues_title(pending_title, row):
                pending_title.section.title = normalize(f"{pending_title.section.title} {row.text}")
                pending_title.title_rows.append(row)
                continue
            pending_title = None

            if heading is not None:
                pending_title = builder.open(heading, row)
            else:
                if builder.current is None:
                    builder.open(Heading("front", "Préambule"), row)
                builder.current.rows.append(row)

    for node in builder.nodes:
        node.section.blocks = _make_blocks(node.rows, page_height)
    for root in builder.roots:
        _fix_page_ranges(root)
    return builder.roots


def _continues_title(node: _Node, row: Row) -> bool:
    """A heading title wrapping onto the next line: same style, aligned, directly below."""
    last = node.title_rows[-1]
    title_x = last.spans[-1].bbox[0]
    return (
        node.section.kind in {"chapter", "article", "subarticle", "term", "front"}
        and row.page == last.page
        and row.bold
        and abs(row.lead.size - last.lead.size) < 0.5
        and row.lead.color == last.lead.color
        and abs(row.bbox[0] - title_x) < 2
        and 0 < row.baseline - last.baseline <= PARAGRAPH_GAP
    )


def _fix_page_ranges(section: Section) -> int:
    pages = [section.page_start] + [b.page for b in section.blocks]
    pages += [_fix_page_ranges(c) for c in section.children]
    section.page_end = max(pages)
    return section.page_end


# --- Entry point ------------------------------------------------------------------------------------------


def parse_pdf(
    path: Path, *, doc_id: str, source_sha256: str, profile: LayoutProfile
) -> tuple[SectionTree, list[list[Row]]]:
    """Parse a PDF into a section tree. Also returns the cleaned rows of each page (used by the TOC check)."""
    with pymupdf.open(path) as doc:
        page_height = doc[0].rect.height
        rows = strip_page_furniture(extract_rows(doc), page_height)
        tree = SectionTree(
            doc_id=doc_id,
            source_sha256=source_sha256,
            parser=f"pymupdf-rules/{profile.name}@{PARSER_VERSION}",
            page_count=doc.page_count,
            sections=build_tree(rows, profile, page_height),
        )
    return tree, rows

"""Check a parsed section tree against the table of contents printed in the document."""

import re
from dataclasses import asdict, dataclass

from isitcovered.ingestion.parse import Row
from isitcovered.models.sections import SectionTree

_CHAPTER_RE = re.compile(r"^Chapitre\s+([IVXLC]+)\s*[-–:]\s*(.+)$")
_ARTICLE_RE = re.compile(r"^Article\s+(\d+)\s*[-–:]\s*(.+)$")
_ENTRY_RE = re.compile(r"^(.*?)\s*(\d+)$")


@dataclass
class TocEntry:
    kind: str  # chapter | article | front
    number: str | None
    title: str
    page: int


def _norm(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").casefold()
    return re.sub(r"\s+", " ", text).strip(" :.")


def read_toc(rows: list[Row], *, ignore: set[str]) -> list[TocEntry]:
    """Parse TOC rows ("<title> <page>"); a title without page number continues on the next row."""
    entries: list[TocEntry] = []
    pending = ""
    for row in rows:
        if row.text in ignore:
            continue
        text = f"{pending} {row.text}".strip()
        if not (m := _ENTRY_RE.match(text)):
            pending = text
            continue
        pending = ""
        label, page = m[1], int(m[2])
        if c := _CHAPTER_RE.match(label):
            entries.append(TocEntry("chapter", c[1], c[2], page))
        elif a := _ARTICLE_RE.match(label):
            entries.append(TocEntry("article", a[1], a[2], page))
        else:
            entries.append(TocEntry("front", None, label, page))
    return entries


def check_toc(entries: list[TocEntry], tree: SectionTree, accepted: dict[str, str] | None = None) -> dict:
    """Compare TOC entries with the tree.

    `accepted` maps a section id to the reason why its discrepancy with the printed TOC is expected
    (an error in the document itself, checked by a human).
    """
    accepted = accepted or {}
    sections = list(tree.walk())
    seen: set[str] = set()
    results = []
    for entry in entries:
        if entry.kind == "front":
            match = next(
                (s for s in sections if s.kind == "front" and _norm(s.title) == _norm(entry.title)), None
            )
        else:
            match = next((s for s in sections if s.kind == entry.kind and s.number == entry.number), None)
        problems = []
        if match is None:
            problems.append("missing")
        else:
            seen.add(match.id)
            if _norm(match.title) != _norm(entry.title):
                problems.append("title")
            if match.page_start != entry.page:
                problems.append("page")
        results.append(
            asdict(entry)
            | {
                "section_id": match.id if match else None,
                "parsed_title": match.title if match else None,
                "parsed_page": match.page_start if match else None,
                "problems": problems,
                "accepted": accepted.get(match.id) if match and problems else None,
            }
        )
    extra = [s.id for s in sections if s.kind in {"chapter", "article"} and s.id not in seen]
    mismatches = sum(1 for r in results if r["problems"] and not r["accepted"])
    return {
        "doc_id": tree.doc_id,
        "parser": tree.parser,
        "toc_entries": len(entries),
        "mismatches": mismatches,
        "accepted_discrepancies": sum(1 for r in results if r["accepted"]),
        "extra_in_tree": extra,
        "ok": bool(entries) and mismatches == 0 and not extra,
        "entries": results,
    }

"""Extraction units: the pieces of a contract sent, one per call, to the extraction LLM (ADR 0008).

A unit is an article, or a sub-article of an article listed as "split" (Ethias art. 3, whose 20 sub-articles
are each a base guarantee). It carries its path of titles, the titles of its sibling sections, the own blocks
of its ancestors (e.g. "This guarantee is only granted if…" at the top of an article, or a chapter's scope
sentence) as context, and every block of the unit with a stable reference: "<section_id>#<n>", n >= 1 in block
order (as on the annotated PDF), "#0" for the section title, which is citable when a sub-article has no text
of its own. References are computed from the approved tree; the parser is left untouched.
"""

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from isitcovered.models.sections import BBox, Section, SectionTree


@dataclass(frozen=True)
class UnitPlan:
    chapters: tuple[str, ...]  # chapters to extract, in order
    split_articles: frozenset[str] = frozenset()  # articles extracted sub-article by sub-article


# Phase 1: chapters I to IV of Ethias (scope, base and optional guarantees, extensions); obligations and
# indemnity rules (V, VI) are out of scope, the lexicon is converted by code (ingestion/definitions.py).
UNIT_PLANS: dict[str, UnitPlan] = {
    "be-ethias-habitation-2025-03": UnitPlan(("ch-i", "ch-ii", "ch-iii", "ch-iv"), frozenset({"art-3"})),
}

NUMBER_PREFIXES = {"chapter": "Chapitre ", "article": "Article "}


def section_label(section: Section) -> str:
    if section.number is None:
        return section.title
    return f"{NUMBER_PREFIXES.get(section.kind, '')}{section.number} – {section.title}"


class UnitBlock(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ref: str  # "<section_id>#<n>"
    section_id: str
    kind: str  # "title" for #0, otherwise the parser's block kind
    text: str
    page: int
    bbox: BBox
    italic: list[str] = []
    context: bool = False  # own block of an ancestor section, given as context


class ExtractionUnit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str  # section id of the unit
    doc_id: str
    section_path: list[str]  # labels from the chapter down to the unit
    sibling_titles: list[str]
    blocks: list[UnitBlock]

    def block(self, ref: str) -> UnitBlock:
        for b in self.blocks:
            if b.ref == ref:
                return b
        raise KeyError(ref)

    def section_ids(self) -> list[str]:
        return list(dict.fromkeys(b.section_id for b in self.blocks if not b.context))

    def render(self) -> str:
        """Plain-text view of the unit, as given to the LLM."""
        lines = [f"Emplacement : {' > '.join(self.section_path)}"]
        if self.sibling_titles:
            lines.append(f"Sections voisines : {' ; '.join(self.sibling_titles)}")
        context = [b for b in self.blocks if b.context]
        if context:
            lines += ["", "Contexte (texte propre aux niveaux supérieurs) :", *map(_render_block, context)]
        lines += ["", "Texte de l'unité :", *(_render_block(b) for b in self.blocks if not b.context)]
        return "\n".join(lines)


def _render_block(block: UnitBlock) -> str:
    kind = "titre, " if block.kind == "title" else ""
    line = f"[{block.ref}] ({kind}p. {block.page}) {block.text}"
    if block.italic:
        line += f"  {{italique : {' | '.join(block.italic)}}}"
    return line


def block_refs(section: Section) -> list[UnitBlock]:
    """The title (#0) and own blocks (#1…) of one section."""
    title = UnitBlock(
        ref=f"{section.id}#0",
        section_id=section.id,
        kind="title",
        text=section.title,
        page=section.page_start,
        bbox=section.bbox,
    )
    own = [
        UnitBlock(
            ref=f"{section.id}#{n}",
            section_id=section.id,
            kind=b.kind,
            text=b.text,
            page=b.page,
            bbox=b.bbox,
            italic=b.italic,
        )
        for n, b in enumerate(section.blocks, start=1)
    ]
    return [title, *own]


def _unit(doc_id: str, section: Section, ancestors: list[Section], siblings: list[Section]) -> ExtractionUnit:
    context = [b.model_copy(update={"context": True}) for a in ancestors for b in block_refs(a)[1:]]
    body = [b for s in section.walk() for b in block_refs(s)]
    return ExtractionUnit(
        id=section.id,
        doc_id=doc_id,
        section_path=[section_label(s) for s in (*ancestors, section)],
        sibling_titles=[section_label(s) for s in siblings if s is not section],
        blocks=context + body,
    )


def build_units(tree: SectionTree, plan: UnitPlan | None = None) -> list[ExtractionUnit]:
    plan = plan or UNIT_PLANS[tree.doc_id]
    roots = {s.id: s for s in tree.sections}
    units = []
    for chapter_id in plan.chapters:
        chapter = roots[chapter_id]
        articles = [s for s in chapter.children if s.kind == "article"]
        for article in articles:
            if article.id in plan.split_articles:
                for sub in article.children:
                    units.append(_unit(tree.doc_id, sub, [chapter, article], article.children))
            else:
                units.append(_unit(tree.doc_id, article, [chapter], articles))
    return units

"""Lexicon → definitions, by code (ADR 0011): one Definition per `term` section, quoted block by block.

Definitions found outside the lexicon ("Par contenu, nous entendons…") are extracted by the LLM instead.
"""

from isitcovered.ingestion.units import block_refs, section_label
from isitcovered.models.extraction import Definition, Quote, Source
from isitcovered.models.sections import Section, SectionTree


def lexicon_definitions(tree: SectionTree) -> list[Definition]:
    definitions = []
    for chapter in tree.sections:
        for term in (s for s in chapter.walk() if s.kind == "term"):
            definitions.append(_definition(tree.doc_id, chapter, term))
    return definitions


def _definition(doc_id: str, chapter: Section, term: Section) -> Definition:
    blocks = block_refs(term)[1:]
    if not blocks:
        raise ValueError(f"{term.id}: lexicon entry without text")
    quotes = [Quote(block_ref=b.ref, text=b.text, page=b.page, bbox=b.bbox) for b in blocks]
    return Definition(
        term=term.title,
        text="\n".join(b.text for b in blocks),
        origin="lexicon",
        source=Source(
            doc_id=doc_id,
            section_id=term.id,
            section_path=[section_label(chapter), term.title],
            quotes=quotes,
        ),
    )

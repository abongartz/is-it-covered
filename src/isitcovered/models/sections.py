"""Section tree of a contract document, as produced by the structural parser."""

from collections.abc import Iterator
from typing import Literal

from pydantic import BaseModel, ConfigDict

BBox = tuple[float, float, float, float]  # x0, y0, x1, y1 in PDF points, origin at the top-left of the page

SectionKind = Literal["front", "chapter", "article", "subarticle", "heading", "term"]
BlockKind = Literal["paragraph", "list_item", "label", "footnote"]


class TextBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: BlockKind
    text: str
    page: int
    bbox: BBox
    italic: list[str] = []  # italic runs; in many contracts, italics mark terms defined in the lexicon


class Section(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str  # stable, derived from the numbering (e.g. "art-4.2")
    kind: SectionKind
    number: str | None = None
    title: str
    level: int
    page_start: int
    page_end: int
    bbox: BBox  # heading position on page_start
    blocks: list[TextBlock] = []
    children: list["Section"] = []

    def walk(self) -> Iterator["Section"]:
        yield self
        for child in self.children:
            yield from child.walk()


class SectionTree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str
    source_sha256: str
    parser: str  # parser name, layout profile and version
    page_count: int
    sections: list[Section]

    def walk(self) -> Iterator[Section]:
        for section in self.sections:
            yield from section.walk()

    def structure(self) -> dict:
        """The tree without the contract text (publishable): blocks are replaced by counts."""

        def strip(section: Section) -> dict:
            data = section.model_dump(exclude={"blocks", "children"})
            data["blocks"] = len(section.blocks)
            data["chars"] = sum(len(b.text) for b in section.blocks)
            data["children"] = [strip(c) for c in section.children]
            return data

        header = self.model_dump(exclude={"sections"})
        return header | {"sections": [strip(s) for s in self.sections]}

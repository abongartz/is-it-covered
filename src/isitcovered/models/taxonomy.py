"""Taxonomy (data/taxonomy.yaml): concepts on the peril axis, plus facets (assets, locations, status).

Concepts orient the selection of candidate guarantees; they never define anything (the meaning always comes
from the contract). Ids are stable: never renamed nor reused; a retired id is deprecated with a pointer.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

ID = r"^[a-z][a-z0-9_]*$"
OTHER = "other"


class Concept(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=ID)
    label: str
    description: str
    examples: list[str] = []  # claims as a policyholder would describe them
    includes: list[str] = []
    excludes: list[str] = []
    deprecated_by: str | None = None


class FacetValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=ID)
    label: str
    description: str = ""


class Facets(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    assets: list[FacetValue]
    locations: list[FacetValue]
    status: list[FacetValue]


class Taxonomy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: int = Field(ge=1)
    concepts: list[Concept]
    facets: Facets

    @model_validator(mode="after")
    def _valid(self) -> "Taxonomy":
        groups = {
            "concepts": self.concepts,
            "assets": self.facets.assets,
            "locations": self.facets.locations,
            "status": self.facets.status,
        }
        for name, items in groups.items():
            ids = [i.id for i in items]
            duplicates = sorted({i for i in ids if ids.count(i) > 1})
            if duplicates:
                raise ValueError(f"duplicate {name} ids: {duplicates}")
        ids = {c.id for c in self.concepts}
        if OTHER not in ids:
            raise ValueError(f"the taxonomy needs the {OTHER!r} concept")
        for c in self.concepts:
            if c.deprecated_by and c.deprecated_by not in ids:
                raise ValueError(f"{c.id}: deprecated_by points to unknown concept {c.deprecated_by!r}")
        return self

    @property
    def active_concepts(self) -> list[Concept]:
        return [c for c in self.concepts if not c.deprecated_by]

    def concept_ids(self) -> set[str]:
        return {c.id for c in self.concepts}

    @classmethod
    def load(cls, path: Path) -> "Taxonomy":
        return cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))

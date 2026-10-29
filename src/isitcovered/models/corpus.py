"""Corpus manifest: one entry per (country, insurer, product, edition) document."""

from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class ManifestDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^(be|lu)-[a-z0-9]+(-[a-z0-9]+)*-\d{4}-\d{2}$")
    country: Literal["BE", "LU"]
    insurer: str
    product: str
    doc_type: Literal["cg", "ipid"]
    language: Literal["fr", "nl", "de", "en"]
    edition_ref: str  # reference printed in the document
    edition_date: str = Field(pattern=r"^\d{4}-\d{2}$")  # edition month printed in the document
    source_url: HttpUrl
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    retrieved_at: date
    pages: int = Field(gt=0)

    @property
    def filename(self) -> str:
        return f"{self.id}.pdf"


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    documents: list[ManifestDocument]

    @model_validator(mode="after")
    def _unique_ids(self) -> "Manifest":
        ids = [d.id for d in self.documents]
        duplicates = {i for i in ids if ids.count(i) > 1}
        if duplicates:
            raise ValueError(f"duplicate document ids: {sorted(duplicates)}")
        return self

    def get(self, doc_id: str) -> ManifestDocument:
        for doc in self.documents:
            if doc.id == doc_id:
                return doc
        raise KeyError(doc_id)

    @classmethod
    def load(cls, path: Path) -> "Manifest":
        return cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))

"""Structured content of a contract: guarantees, exclusions, definitions, each with its source.

Fields computed by code (ids, pages, coordinates, targeted guarantees, concepts, the `cp_subscription`
condition) are never produced by the LLM, which only fills dedicated output schemas (see ingestion/).
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from isitcovered.models.sections import BBox

BLOCK_REF = (
    r"^[a-z0-9][A-Za-z0-9.\-/]*#\d+$"  # "<section_id>#<n>": n >= 1 in block order, 0 = the section title
)

ConditionKind = Literal["peril", "asset", "location", "circumstance", "obligation", "cp_subscription"]
GuaranteeKind = Literal["base", "optional", "extension"]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Quote(_Model):
    block_ref: str = Field(pattern=BLOCK_REF)
    text: str = Field(min_length=1)  # passage of the source block (never the LLM's wording)
    page: int = Field(ge=1)
    bbox: BBox  # of the block, or of the title for "#0"

    @property
    def section_id(self) -> str:
        return self.block_ref.rsplit("#", 1)[0]


class Source(_Model):
    doc_id: str
    section_id: str
    section_path: list[str]  # titles from the chapter down to the section
    quotes: list[Quote] = Field(min_length=1)


class Condition(_Model):
    id: str
    kind: ConditionKind
    text: str  # short restatement, for display; the meaning comes from the quotes
    defined_terms: list[str] = []
    source: Source


class GeneralCondition(Condition):
    """Condition that applies to every guarantee of the listed kinds (e.g. Ethias art. 2 #1)."""

    applies_to: list[GuaranteeKind] = ["base", "optional"]


class ConceptLink(_Model):
    concept: str  # taxonomy concept id
    confidence: float = Field(ge=0, le=1)


class Guarantee(_Model):
    id: str  # "<doc>/g/<slug>"
    name: str  # heading used by the contract
    section_id: str
    kind: GuaranteeKind
    cp_optional: bool  # only granted if the special conditions (CP) say so
    concepts: list[ConceptLink] = []  # filled by the linking step
    assets: list[str] = []  # taxonomy facet ids
    locations: list[str] = []  # taxonomy facet ids
    conditions: list[Condition] = []
    source: Source


class Exclusion(_Model):
    id: str  # "<doc>/x/<slug>"
    scope: Literal["general", "specific"]
    guarantee_ids: list[str] = []  # set by code for specific exclusions
    triggers: list[Condition] = Field(min_length=1)  # cumulative: all must be met
    exceptions: list[Condition] = []  # any met exception lifts the exclusion
    defined_terms: list[str] = []
    source: Source


class Definition(_Model):
    term: str
    text: str
    origin: Literal["lexicon", "inline"]
    source: Source


class ContractExtraction(_Model):
    doc_id: str
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    parser: str
    model: str  # provider/model of the extraction route
    prompt_version: str  # hash of the prompt files
    created_at: datetime
    general_conditions: list[GeneralCondition] = []
    guarantees: list[Guarantee] = []
    exclusions: list[Exclusion] = []
    definitions: list[Definition] = []

    @model_validator(mode="after")
    def _consistent(self) -> "ContractExtraction":
        ids = [g.id for g in self.guarantees] + [x.id for x in self.exclusions]
        ids += [c.id for c in self.general_conditions]
        ids += [c.id for g in self.guarantees for c in g.conditions]
        ids += [c.id for x in self.exclusions for c in (*x.triggers, *x.exceptions)]
        duplicates = sorted({i for i in ids if ids.count(i) > 1})
        if duplicates:
            raise ValueError(f"duplicate ids: {duplicates}")
        guarantee_ids = {g.id for g in self.guarantees}
        for x in self.exclusions:
            if x.scope == "general" and x.guarantee_ids:
                raise ValueError(f"{x.id}: a general exclusion targets no specific guarantee")
            if x.scope == "specific" and not x.guarantee_ids:
                raise ValueError(f"{x.id}: a specific exclusion must target a guarantee")
            unknown = set(x.guarantee_ids) - guarantee_ids
            if unknown:
                raise ValueError(f"{x.id}: unknown guarantees {sorted(unknown)}")
        return self

    def guarantee(self, guarantee_id: str) -> Guarantee:
        for g in self.guarantees:
            if g.id == guarantee_id:
                return g
        raise KeyError(guarantee_id)

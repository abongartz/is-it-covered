"""Typed facts of one claim, produced by the online `facts` step from the user's description."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from isitcovered.models.extraction import ConceptLink

InsuredStatus = Literal["owner", "tenant", "other_occupant", "unknown"]


class ClaimFacts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event: str  # what happened, restated briefly
    cause: str | None  # known cause, if any
    damaged_assets: list[str]  # in the user's words
    asset_facets: list[str]  # taxonomy facet ids
    location: str | None  # where the damage happened, in the user's words
    location_facets: list[str]  # taxonomy facet ids
    insured_status: InsuredStatus
    circumstances: list[str]  # other stated facts (e.g. "the room was not locked")
    unknown_facts: list[str]  # facts the user says they do not know
    perils: list[ConceptLink]  # activated taxonomy concepts (several allowed: recall first)

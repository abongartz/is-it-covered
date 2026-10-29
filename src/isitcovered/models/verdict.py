"""Judgements on elementary conditions (LLM) and the verdict built from them (code, never the LLM)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from isitcovered.models.extraction import Quote

JudgementStatus = Literal["met", "not_met", "unknown", "ambiguous"]
TriState = Literal["true", "false", "unknown"]
Verdict = Literal["covered", "not_covered", "undetermined"]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Judgement(_Model):
    condition_id: str  # condition, exclusion trigger or exclusion exception
    status: JudgementStatus
    justification: str
    quote: Quote | None = None  # verified against the clause before display; None if invalid or absent
    missing_fact: str | None = None  # what would settle an `unknown`


class GuaranteeOutcome(_Model):
    guarantee_id: str
    result: TriState
    unmet_conditions: list[str] = []  # condition ids judged not_met
    applicable_exclusions: list[str] = []  # exclusion ids that apply
    open_conditions: list[str] = []  # condition ids still unknown or ambiguous


class ClaimVerdict(_Model):
    verdict: Verdict
    reason: Literal["guarantee_met", "all_ruled_out", "open_conditions", "no_candidate"]
    outcomes: list[GuaranteeOutcome] = []
    missing_facts: list[str] = []
    ambiguous_conditions: list[str] = []

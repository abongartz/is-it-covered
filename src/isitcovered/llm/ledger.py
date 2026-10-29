"""Cost ledger: one JSON line per LLM call made by the offline scripts (data/costs/ledger.jsonl, committed).

A record holds when, which route and model, the token counts, the estimated cost and the outcome. It never
holds prompt or output content, nor any key. Tests and the online app never write to it (no default path).
"""

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from isitcovered.llm.base import Usage
from isitcovered.llm.config import Route, RouteConfig


class CallRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    at: datetime
    route: Route
    model: str  # provider/model
    effort: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    cost_usd: float
    outcome: str  # "ok" or the error class name

    @classmethod
    def of(
        cls, route: Route, config: RouteConfig, usage: Usage, cost_usd: float, outcome: str
    ) -> "CallRecord":
        return cls(
            at=datetime.now(UTC).replace(microsecond=0),
            route=route,
            model=config.label,
            effort=config.effort,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cache_read_tokens=usage.cache_read_tokens,
            cache_write_tokens=usage.cache_write_tokens,
            cost_usd=round(cost_usd, 6),
            outcome=outcome,
        )


class CostLedger:
    def __init__(self, path: Path):
        self.path = path

    def append(self, record: CallRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(record.model_dump_json() + "\n")

    def records(self) -> list[CallRecord]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        return [CallRecord.model_validate_json(line) for line in lines if line.strip()]

    def total_usd(self) -> float:
        return sum(r.cost_usd for r in self.records())

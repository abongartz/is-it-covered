"""Routes: each kind of call has its own provider, model and effort, overridable by environment variables.

    ISITCOVERED_MODEL_<ROUTE>=<provider>/<model>    e.g. ISITCOVERED_MODEL_FACTS=anthropic/claude-sonnet-5-5
    ISITCOVERED_EFFORT_<ROUTE>=<effort>             e.g. ISITCOVERED_EFFORT_FACTS=low

Model ids are exact versions, never aliases (see ADR 0006).
"""

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, get_args

Effort = Literal["low", "medium", "high", "xhigh", "max"]
PROVIDERS = ("anthropic",)
_ALIAS = re.compile(r"latest", re.IGNORECASE)


class Route(StrEnum):
    INGESTION = "ingestion"  # offline extraction of guarantees, exclusions, definitions
    LINKING = "linking"  # offline linking of guarantees to taxonomy concepts
    FACTS = "facts"  # online: claim description -> typed facts
    EVALUATION = "evaluation"  # online: one candidate guarantee -> condition judgements


@dataclass(frozen=True)
class RouteConfig:
    provider: str
    model: str
    effort: Effort

    @property
    def label(self) -> str:
        return f"{self.provider}/{self.model}"


DEFAULTS: dict[Route, RouteConfig] = {
    Route.INGESTION: RouteConfig("anthropic", "claude-sonnet-5-5", "high"),
    Route.LINKING: RouteConfig("anthropic", "claude-sonnet-5-5", "high"),
    Route.FACTS: RouteConfig("anthropic", "claude-haiku-5-5", "medium"),
    Route.EVALUATION: RouteConfig("anthropic", "claude-haiku-5-5", "medium"),
}


def resolve(route: Route, env: Mapping[str, str] | None = None) -> RouteConfig:
    env = os.environ if env is None else env
    default = DEFAULTS[route]
    provider, model = default.provider, default.model
    if override := env.get(f"ISITCOVERED_MODEL_{route.name}"):
        provider, sep, model = override.partition("/")
        if not sep or not provider or not model:
            raise ValueError(f"ISITCOVERED_MODEL_{route.name} must look like '<provider>/<model>'")
    if provider not in PROVIDERS:
        raise ValueError(f"unknown LLM provider {provider!r} (known: {', '.join(PROVIDERS)})")
    if _ALIAS.search(model):
        raise ValueError(f"model {model!r} is an alias: use an exact model version")
    effort = env.get(f"ISITCOVERED_EFFORT_{route.name}", default.effort)
    if effort not in get_args(Effort):
        raise ValueError(f"ISITCOVERED_EFFORT_{route.name} must be one of {get_args(Effort)}")
    return RouteConfig(provider, model, effort)

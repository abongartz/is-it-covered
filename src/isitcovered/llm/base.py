"""Provider-independent interface for structured LLM calls.

Every LLM call of the project goes through an LLMClient: the caller gives a Pydantic schema and gets back a
validated instance plus the token usage and estimated cost. Provider SDKs are only imported by adapters.
"""

from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel

from isitcovered.llm.config import Route, RouteConfig


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0  # uncached input
    output_tokens: int = 0  # includes thinking tokens
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @property
    def prompt_tokens(self) -> int:
        """Total prompt size, which selects the pricing tier."""
        return self.input_tokens + self.cache_read_tokens + self.cache_write_tokens

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            self.input_tokens + other.input_tokens,
            self.output_tokens + other.output_tokens,
            self.cache_read_tokens + other.cache_read_tokens,
            self.cache_write_tokens + other.cache_write_tokens,
        )


@dataclass(frozen=True)
class LLMResult[T: BaseModel]:
    output: T
    route: Route
    config: RouteConfig
    usage: Usage
    cost_usd: float


class LLMError(Exception):
    """Base class. Messages never contain the API key, the prompt or the model output."""


class LLMConfigError(LLMError):
    """Missing key, unknown provider or model without a price."""


class LLMUnavailableError(LLMError):
    """The provider could not be reached or rejected the request (auth, quota, rate limit, server error)."""


class LLMRefusalError(LLMError):
    """The model declined to answer."""


class LLMTruncatedError(LLMError):
    """The output hit max_tokens (or the context window) before the structured output was complete."""


class LLMInvalidOutputError(LLMError):
    """The output does not validate against the requested schema."""


Message = dict[str, str]  # {"role": "user" | "assistant", "content": "..."}


class LLMClient(Protocol):
    def structured[T: BaseModel](
        self, system: str, messages: list[Message], schema: type[T], *, max_tokens: int, route: Route
    ) -> LLMResult[T]:
        """Run one call whose output must validate against `schema`.

        Usage and cost are recorded even when the call fails after tokens were spent.
        """
        ...

    def count_tokens(
        self, system: str, messages: list[Message], schema: type[BaseModel], *, route: Route
    ) -> int:
        """Prompt size in tokens for this route's model (free, used for cost estimates before a run)."""
        ...

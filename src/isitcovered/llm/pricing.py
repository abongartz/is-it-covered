"""Estimated cost of a call, in USD, from the provider's public price list.

Prices in USD per million tokens, read on 2026-10-29 (https://platform.claude.com/docs/en/about-claude/pricing).
Cache reads cost 0.1x and 5-minute cache writes 1.25x the input price. Some models have a second rate card for
long prompts. A model without a price is refused: the cost of every call must be known.
"""

from dataclasses import dataclass

from isitcovered.llm.base import LLMConfigError, Usage

CACHE_READ_FACTOR = 0.1
CACHE_WRITE_FACTOR = 1.25


@dataclass(frozen=True)
class RateCard:
    input: float
    output: float


@dataclass(frozen=True)
class ModelPrice:
    base: RateCard
    long_prompt: RateCard | None = None  # applies when the prompt exceeds long_prompt_threshold tokens
    long_prompt_threshold: int = 0

    def card(self, prompt_tokens: int) -> RateCard:
        if self.long_prompt and prompt_tokens > self.long_prompt_threshold:
            return self.long_prompt
        return self.base


PRICES: dict[str, ModelPrice] = {
    "anthropic/claude-sonnet-5-5": ModelPrice(RateCard(2.00, 10.00)),
    "anthropic/claude-haiku-5-5": ModelPrice(RateCard(0.10, 0.50), RateCard(0.50, 2.50), 100_000),
}


def price_of(model_label: str) -> ModelPrice:
    try:
        return PRICES[model_label]
    except KeyError:
        raise LLMConfigError(f"no price recorded for {model_label}: add it to llm/pricing.py") from None


def estimate_cost(model_label: str, usage: Usage) -> float:
    card = price_of(model_label).card(usage.prompt_tokens)
    return (
        usage.input_tokens * card.input
        + usage.cache_read_tokens * card.input * CACHE_READ_FACTOR
        + usage.cache_write_tokens * card.input * CACHE_WRITE_FACTOR
        + usage.output_tokens * card.output
    ) / 1_000_000

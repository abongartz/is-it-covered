"""Anthropic adapter: the only module (with the future ingestion batch code) that imports the `anthropic` SDK.

API points (see ADR 0005 to 0007): structured outputs through `output_config.format` (JSON schema generated
from the Pydantic model), `max_tokens` always set, no `temperature` (refused by the API), effort per route,
adaptive thinking left on by default, the system prompt marked for prompt caching (ignored below the model's
minimum cacheable size). `stop_reason` is checked before the output is read. SDK errors are translated into
LLMError subclasses without their details, so that no message can carry a header, a prompt or a key.
"""

import logging
from collections.abc import Callable

import anthropic
from pydantic import BaseModel, ValidationError

from isitcovered.llm.base import (
    LLMConfigError,
    LLMInvalidOutputError,
    LLMRefusalError,
    LLMResult,
    LLMTruncatedError,
    LLMUnavailableError,
    Message,
    Usage,
)
from isitcovered.llm.config import Route, RouteConfig, resolve
from isitcovered.llm.ledger import CallRecord, CostLedger
from isitcovered.llm.pricing import estimate_cost, price_of

# HTTP logs of the SDK stay off: at DEBUG/INFO level they can include request details.
for _name in ("anthropic", "httpx2", "httpx", "httpcore"):
    logging.getLogger(_name).setLevel(logging.WARNING)

TIMEOUT_S = 600.0  # explicit, so the SDK does not refuse non-streaming calls with a large max_tokens
MAX_RETRIES = 2  # SDK retries on connection errors, 408, 409, 429 and 5xx

CallObserver = Callable[[CallRecord], None]


class AnthropicClient:
    def __init__(
        self,
        api_key: str,
        *,
        ledger: CostLedger | None = None,
        on_call: CallObserver | None = None,
        resolve_route: Callable[[Route], RouteConfig] = resolve,
        http_client: object
        | None = None,  # tests only: an anthropic.DefaultHttpxClient with a mock transport
    ):
        if not api_key:
            raise LLMConfigError("no API key")
        self._sdk = anthropic.Anthropic(
            api_key=api_key, timeout=TIMEOUT_S, max_retries=MAX_RETRIES, http_client=http_client
        )
        self._ledger = ledger
        self._on_call = on_call
        self._resolve = resolve_route

    def _config(self, route: Route) -> RouteConfig:
        config = self._resolve(route)
        if config.provider != "anthropic":
            raise LLMConfigError(f"route {route} is configured for {config.provider}, not anthropic")
        price_of(config.label)  # fail before spending anything if the model has no price
        return config

    @staticmethod
    def _request(system: str, messages: list[Message], schema: type[BaseModel], config: RouteConfig) -> dict:
        return {
            "model": config.model,
            "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            "messages": messages,
            "output_config": {
                "effort": config.effort,
                "format": {
                    "type": "json_schema",
                    "schema": anthropic.transform_schema(schema.model_json_schema()),
                },
            },
        }

    def _record(self, route: Route, config: RouteConfig, usage: Usage, outcome: str) -> float:
        cost = estimate_cost(config.label, usage)
        record = CallRecord.of(route, config, usage, cost, outcome)
        if self._ledger is not None:
            self._ledger.append(record)
        if self._on_call is not None:
            self._on_call(record)
        return cost

    def structured[T: BaseModel](
        self, system: str, messages: list[Message], schema: type[T], *, max_tokens: int, route: Route
    ) -> LLMResult[T]:
        config = self._config(route)
        params = self._request(system, messages, schema, config)
        try:
            response = self._sdk.messages.create(max_tokens=max_tokens, **params)
        except anthropic.APIError as exc:
            raise _translate(exc) from None

        u = response.usage
        usage = Usage(
            input_tokens=u.input_tokens,
            output_tokens=u.output_tokens,
            cache_read_tokens=u.cache_read_input_tokens or 0,
            cache_write_tokens=u.cache_creation_input_tokens or 0,
        )
        error: Exception | None = None
        output: T | None = None
        if response.stop_reason == "refusal":
            category = response.stop_details.category if response.stop_details else None
            error = LLMRefusalError(f"the model declined to answer (category: {category})")
        elif response.stop_reason in ("max_tokens", "model_context_window_exceeded"):
            error = LLMTruncatedError(f"output cut off ({response.stop_reason}, max_tokens={max_tokens})")
        else:
            text = "".join(block.text for block in response.content if block.type == "text")
            try:
                output = schema.model_validate_json(text)
            except ValidationError as exc:
                error = LLMInvalidOutputError(
                    f"output does not match {schema.__name__} ({exc.error_count()} errors)"
                )

        cost = self._record(route, config, usage, "ok" if error is None else type(error).__name__)
        if error is not None:
            raise error
        assert output is not None
        return LLMResult(output=output, route=route, config=config, usage=usage, cost_usd=cost)

    def count_tokens(
        self, system: str, messages: list[Message], schema: type[BaseModel], *, route: Route
    ) -> int:
        config = self._config(route)
        params = self._request(system, messages, schema, config)
        params["output_config"] = {"format": params["output_config"]["format"]}
        try:
            return self._sdk.messages.count_tokens(**params).input_tokens
        except anthropic.APIError as exc:
            raise _translate(exc) from None


def _translate(exc: anthropic.APIError) -> Exception:
    """Map an SDK error to an LLMError carrying only its kind and HTTP status."""
    if isinstance(exc, anthropic.AuthenticationError | anthropic.PermissionDeniedError):
        return LLMUnavailableError(f"API key rejected (HTTP {exc.status_code})")
    if isinstance(exc, anthropic.NotFoundError):
        return LLMConfigError("unknown model or endpoint (HTTP 404)")
    if isinstance(exc, anthropic.RateLimitError):
        return LLMUnavailableError("rate limit or spend limit reached (HTTP 429)")
    if isinstance(exc, anthropic.BadRequestError):
        # The API's own explanation (a parameter problem) is kept: it never echoes headers or the key.
        body = exc.body if isinstance(exc.body, dict) else {}
        detail = body.get("error", {}).get("message", "") if isinstance(body.get("error"), dict) else ""
        return LLMConfigError(f"request rejected by the API (HTTP 400): {detail[:200]}")
    if isinstance(exc, anthropic.APIStatusError):
        return LLMUnavailableError(f"provider error (HTTP {exc.status_code})")
    if isinstance(exc, anthropic.APITimeoutError):
        return LLMUnavailableError("provider timeout")
    return LLMUnavailableError("provider unreachable")

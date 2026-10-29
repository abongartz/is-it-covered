import json
import re
from pathlib import Path

import anthropic
import httpx2
import pytest
from pydantic import BaseModel

from isitcovered.llm.anthropic_client import AnthropicClient
from isitcovered.llm.base import (
    LLMConfigError,
    LLMInvalidOutputError,
    LLMRefusalError,
    LLMTruncatedError,
    LLMUnavailableError,
    Usage,
)
from isitcovered.llm.config import DEFAULTS, Route, RouteConfig, resolve
from isitcovered.llm.fake import FakeLLMClient
from isitcovered.llm.keys import LOCAL_ENV_VAR, require_local_api_key
from isitcovered.llm.ledger import CallRecord, CostLedger
from isitcovered.llm.pricing import estimate_cost

ROOT = Path(__file__).resolve().parents[1]
SECRET = "sk-ant-test-0123456789-SECRET"


class Reply(BaseModel):
    answer: str


# --- pricing -----------------------------------------------------------------------------------------------


def test_cost_of_a_haiku_call():
    usage = Usage(input_tokens=100_000, output_tokens=10_000)
    assert estimate_cost("anthropic/claude-haiku-5-5", usage) == pytest.approx(
        (100_000 * 0.10 + 10_000 * 0.50) / 1e6
    )


def test_haiku_long_prompts_use_the_second_rate_card():
    usage = Usage(input_tokens=60_000, cache_read_tokens=50_000, output_tokens=1_000)
    expected = (60_000 * 0.50 + 50_000 * 0.50 * 0.1 + 1_000 * 2.50) / 1e6
    assert estimate_cost("anthropic/claude-haiku-5-5", usage) == pytest.approx(expected)


def test_cache_reads_and_writes_are_priced():
    usage = Usage(input_tokens=1_000, cache_read_tokens=10_000, cache_write_tokens=2_000, output_tokens=500)
    expected = (1_000 * 2 + 10_000 * 2 * 0.1 + 2_000 * 2 * 1.25 + 500 * 10) / 1e6
    assert estimate_cost("anthropic/claude-sonnet-5-5", usage) == pytest.approx(expected)


def test_a_model_without_price_is_refused():
    with pytest.raises(LLMConfigError):
        estimate_cost("anthropic/claude-unknown-1", Usage())


def test_every_default_model_has_a_price():
    for config in DEFAULTS.values():
        estimate_cost(config.label, Usage(input_tokens=1))


# --- routing -----------------------------------------------------------------------------------------------


def test_default_routes():
    assert resolve(Route.INGESTION, {}) == RouteConfig("anthropic", "claude-sonnet-5-5", "high")
    assert resolve(Route.EVALUATION, {}) == RouteConfig("anthropic", "claude-haiku-5-5", "medium")


def test_model_and_effort_are_overridable_per_route():
    env = {
        "ISITCOVERED_MODEL_EVALUATION": "anthropic/claude-sonnet-5-5",
        "ISITCOVERED_EFFORT_EVALUATION": "low",
    }
    assert resolve(Route.EVALUATION, env) == RouteConfig("anthropic", "claude-sonnet-5-5", "low")
    assert resolve(Route.FACTS, env) == DEFAULTS[Route.FACTS]


@pytest.mark.parametrize(
    "env",
    [
        {"ISITCOVERED_MODEL_FACTS": "claude-haiku-5-5"},  # no provider
        {"ISITCOVERED_MODEL_FACTS": "openai/gpt"},  # unknown provider
        {"ISITCOVERED_MODEL_FACTS": "anthropic/claude-sonnet-latest"},  # alias
        {"ISITCOVERED_EFFORT_FACTS": "extreme"},
    ],
)
def test_invalid_overrides_are_refused(env):
    with pytest.raises(ValueError):
        resolve(Route.FACTS, env)


# --- ledger ------------------------------------------------------------------------------------------------


def test_ledger_appends_and_totals(tmp_path):
    ledger = CostLedger(tmp_path / "costs" / "ledger.jsonl")
    assert ledger.total_usd() == 0
    config = DEFAULTS[Route.FACTS]
    ledger.append(CallRecord.of(Route.FACTS, config, Usage(10, 5), 0.0012, "ok"))
    ledger.append(CallRecord.of(Route.FACTS, config, Usage(10, 5), 0.0008, "LLMTruncatedError"))
    assert [r.outcome for r in ledger.records()] == ["ok", "LLMTruncatedError"]
    assert ledger.total_usd() == pytest.approx(0.002)


def test_ledger_records_hold_no_content():
    assert set(CallRecord.model_fields) == {
        "at",
        "route",
        "model",
        "effort",
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "cache_write_tokens",
        "cost_usd",
        "outcome",
    }


# --- fake client -------------------------------------------------------------------------------------------


def test_fake_client_replays_outputs_in_order():
    fake = FakeLLMClient({Route.FACTS: [{"answer": "a"}, Reply(answer="b"), LLMRefusalError("no")]})
    ask = [{"role": "user", "content": "?"}]
    assert fake.structured("s", ask, Reply, max_tokens=10, route=Route.FACTS).output.answer == "a"
    assert fake.structured("s", ask, Reply, max_tokens=10, route=Route.FACTS).output.answer == "b"
    with pytest.raises(LLMRefusalError):
        fake.structured("s", ask, Reply, max_tokens=10, route=Route.FACTS)
    with pytest.raises(AssertionError):
        fake.structured("s", ask, Reply, max_tokens=10, route=Route.FACTS)
    assert len(fake.calls) == 4


# --- Anthropic adapter, against a mocked HTTP transport ---------------------------------------------------


def message(text: str, stop_reason: str = "end_turn", **extra) -> dict:
    return {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "model": "claude-haiku-5-5",
        "content": [{"type": "thinking", "thinking": "", "signature": "sig"}, {"type": "text", "text": text}],
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": 1_000,
            "output_tokens": 200,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
        },
        **extra,
    }


def client_with(responses, tmp_path, requests=None) -> tuple[AnthropicClient, CostLedger]:
    def handler(request: httpx2.Request) -> httpx2.Response:
        if requests is not None:
            requests.append(request)
        status, body = responses(request)
        return httpx2.Response(status, json=body)

    ledger = CostLedger(tmp_path / "ledger.jsonl")
    http = anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(handler))
    return AnthropicClient(
        SECRET, ledger=ledger, http_client=http, resolve_route=lambda r: resolve(r, {})
    ), ledger


ASK = [{"role": "user", "content": "Réponds ok."}]


def test_structured_call_parses_output_and_records_cost(tmp_path):
    requests = []
    client, ledger = client_with(lambda r: (200, message('{"answer": "ok"}')), tmp_path, requests)
    result = client.structured("Système", ASK, Reply, max_tokens=512, route=Route.FACTS)

    assert result.output == Reply(answer="ok")
    assert result.cost_usd == pytest.approx((1_000 * 0.10 + 200 * 0.50) / 1e6)
    assert ledger.records()[0].outcome == "ok"
    assert ledger.records()[0].model == "anthropic/claude-haiku-5-5"

    body = json.loads(requests[0].content)
    assert body["model"] == "claude-haiku-5-5"
    assert body["max_tokens"] == 512
    assert "temperature" not in body
    assert body["output_config"]["effort"] == "medium"
    assert body["output_config"]["format"]["type"] == "json_schema"
    assert body["system"][0]["cache_control"] == {"type": "ephemeral"}


@pytest.mark.parametrize(
    ("response", "error", "outcome"),
    [
        (
            message("", "refusal", stop_details={"type": "refusal", "category": "cyber"}),
            LLMRefusalError,
            None,
        ),
        (message('{"answer": "o', "max_tokens"), LLMTruncatedError, None),
        (message('{"other": 1}'), LLMInvalidOutputError, None),
    ],
)
def test_failed_outputs_raise_but_their_cost_is_recorded(tmp_path, response, error, outcome):
    client, ledger = client_with(lambda r: (200, response), tmp_path)
    with pytest.raises(error):
        client.structured("Système", ASK, Reply, max_tokens=512, route=Route.FACTS)
    assert ledger.records()[0].outcome == error.__name__
    assert ledger.records()[0].cost_usd > 0


@pytest.mark.parametrize(
    ("status", "error"),
    [(401, LLMUnavailableError), (403, LLMUnavailableError), (404, LLMConfigError), (400, LLMConfigError)],
)
def test_api_errors_never_reveal_the_key(tmp_path, status, error):
    body = {"type": "error", "error": {"type": "x", "message": "something about the request"}}
    client, ledger = client_with(lambda r: (status, body), tmp_path)
    with pytest.raises(error) as info:
        client.structured("Système", ASK, Reply, max_tokens=512, route=Route.FACTS)
    assert SECRET not in str(info.value)
    assert info.value.__cause__ is None and info.value.__suppress_context__
    assert ledger.records() == []  # nothing was spent


def test_count_tokens_uses_the_route_model(tmp_path):
    requests = []
    client, ledger = client_with(lambda r: (200, {"input_tokens": 42}), tmp_path, requests)
    assert client.count_tokens("Système", ASK, Reply, route=Route.INGESTION) == 42
    assert requests[0].url.path.endswith("/count_tokens")
    assert json.loads(requests[0].content)["model"] == "claude-sonnet-5-5"
    assert ledger.records() == []


def test_unpriced_model_fails_before_any_request(tmp_path):
    requests = []
    client, _ = client_with(lambda r: (200, message("{}")), tmp_path, requests)
    client._resolve = lambda r: RouteConfig("anthropic", "claude-unknown-1", "low")
    with pytest.raises(LLMConfigError):
        client.structured("Système", ASK, Reply, max_tokens=512, route=Route.FACTS)
    assert requests == []


# --- keys and import boundary ------------------------------------------------------------------------------


def test_missing_local_key_is_a_clear_error():
    with pytest.raises(LLMConfigError, match=LOCAL_ENV_VAR):
        require_local_api_key({})
    assert require_local_api_key({LOCAL_ENV_VAR: SECRET}) == SECRET


ALLOWED_SDK_IMPORTERS = {"src/isitcovered/llm/anthropic_client.py"}
ALLOWED_SDK_IMPORTER_PATTERN = re.compile(r"^src/isitcovered/ingestion/batch\w*\.py$")  # future batch code
SDK_IMPORT = re.compile(r"^\s*(import|from)\s+anthropic\b", re.MULTILINE)


def test_only_the_adapter_imports_the_provider_sdk():
    offenders = []
    for folder in ("src", "app", "scripts"):
        for path in (ROOT / folder).rglob("*.py"):
            rel = path.relative_to(ROOT).as_posix()
            if rel in ALLOWED_SDK_IMPORTERS or ALLOWED_SDK_IMPORTER_PATTERN.match(rel):
                continue
            if SDK_IMPORT.search(path.read_text(encoding="utf-8")):
                offenders.append(rel)
    assert offenders == []

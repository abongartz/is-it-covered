"""Fake LLMClient replaying recorded outputs: every test runs without network or key."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from pydantic import BaseModel

from isitcovered.llm.base import LLMResult, Message, Usage
from isitcovered.llm.config import Route, RouteConfig

FAKE_CONFIG = RouteConfig("fake", "fake-model", "low")


@dataclass
class FakeCall:
    route: Route
    system: str
    messages: list[Message]
    schema: type[BaseModel]
    max_tokens: int


@dataclass
class FakeLLMClient:
    """Returns, for each route, the recorded outputs in order (dicts are validated against the schema).

    An output that is an exception instance is raised instead, to test error paths.
    """

    outputs: Mapping[Route, Sequence[BaseModel | dict | Exception]] = field(default_factory=dict)
    usage: Usage = field(default_factory=lambda: Usage(input_tokens=100, output_tokens=50))
    calls: list[FakeCall] = field(default_factory=list)

    def structured[T: BaseModel](
        self, system: str, messages: list[Message], schema: type[T], *, max_tokens: int, route: Route
    ) -> LLMResult[T]:
        index = sum(1 for c in self.calls if c.route == route)
        self.calls.append(FakeCall(route, system, messages, schema, max_tokens))
        recorded = self.outputs.get(route, [])
        if index >= len(recorded):
            raise AssertionError(f"no recorded output left for route {route} (call #{index + 1})")
        item = recorded[index]
        if isinstance(item, Exception):
            raise item
        output = schema.model_validate(item.model_dump() if isinstance(item, BaseModel) else item)
        return LLMResult(output=output, route=route, config=FAKE_CONFIG, usage=self.usage, cost_usd=0.0)

    def count_tokens(
        self, system: str, messages: list[Message], schema: type[BaseModel], *, route: Route
    ) -> int:
        text = system + "".join(m["content"] for m in messages)
        return len(text) // 4

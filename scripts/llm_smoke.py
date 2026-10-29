"""Smoke test of the LLM layer: one tiny structured call, recorded in the cost ledger.

Usage:
    uv run python scripts/llm_smoke.py --count-only   # free token count, no generation
    uv run python scripts/llm_smoke.py                # one real call (route "facts", < 0.01 USD)

The key is read from the ISITCOVERED_ANTHROPIC_API_KEY environment variable.
"""

import argparse
import sys
from pathlib import Path

from pydantic import BaseModel

from isitcovered.llm.anthropic_client import AnthropicClient
from isitcovered.llm.base import LLMError
from isitcovered.llm.config import Route, resolve
from isitcovered.llm.keys import require_local_api_key
from isitcovered.llm.ledger import CostLedger

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = "Tu vérifies qu'une connexion fonctionne. Réponds uniquement au format demandé."
MESSAGES = [{"role": "user", "content": "Réponds « ok » dans le champ answer."}]
MAX_TOKENS = 1024


class SmokeReply(BaseModel):
    answer: str


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--count-only", action="store_true", help="only count prompt tokens (free)")
    parser.add_argument("--ledger", type=Path, default=ROOT / "data" / "costs" / "ledger.jsonl")
    args = parser.parse_args()

    route = Route.FACTS
    try:
        client = AnthropicClient(require_local_api_key(), ledger=CostLedger(args.ledger))
        print(f"route {route}: {resolve(route).label}, effort {resolve(route).effort}")
        if args.count_only:
            tokens = client.count_tokens(SYSTEM, MESSAGES, SmokeReply, route=route)
            print(f"prompt: {tokens} tokens")
            return 0
        result = client.structured(SYSTEM, MESSAGES, SmokeReply, max_tokens=MAX_TOKENS, route=route)
    except LLMError as exc:
        print(f"ERROR {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    u = result.usage
    print(f"answer: {result.output.answer!r}")
    print(
        f"tokens: {u.input_tokens} in, {u.output_tokens} out, {u.cache_read_tokens} cache read, "
        f"{u.cache_write_tokens} cache write; estimated cost {result.cost_usd:.6f} USD"
    )
    print(f"ledger total: {CostLedger(args.ledger).total_usd():.6f} USD")
    return 0


if __name__ == "__main__":
    sys.exit(main())

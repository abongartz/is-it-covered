"""Where our API key comes from. The key is never written to disk, logged, or put in a message or cache key.

- Local runs (scripts and app): the ISITCOVERED_ANTHROPIC_API_KEY environment variable. Not ANTHROPIC_API_KEY,
  which Claude Code would pick up for its own use.
- Hosted app: st.secrets["ANTHROPIC_API_KEY"], read by the app and passed in explicitly.
"""

import os
from collections.abc import Mapping

from isitcovered.llm.base import LLMConfigError

LOCAL_ENV_VAR = "ISITCOVERED_ANTHROPIC_API_KEY"


def local_api_key(env: Mapping[str, str] | None = None) -> str | None:
    env = os.environ if env is None else env
    return env.get(LOCAL_ENV_VAR) or None


def require_local_api_key(env: Mapping[str, str] | None = None) -> str:
    key = local_api_key(env)
    if not key:
        raise LLMConfigError(f"no API key: set the {LOCAL_ENV_VAR} environment variable")
    return key

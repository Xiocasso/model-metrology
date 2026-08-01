"""Model registry — adding a model means adding an entry here, never editing code.

Pattern copied from model-metrology instruments/stress_probe/stress_probe/
registry.py. claude-haiku-45 is the pinned model of the original identity-os
run; gpt-4o-mini and kimi-k3 are placeholders gated on their API keys being
present.
"""

from __future__ import annotations

from dataclasses import dataclass

MOONSHOT_URL = "https://api.moonshot.ai/v1/chat/completions"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"


@dataclass(frozen=True)
class ModelSpec:
    key: str  # registry key, used in trial ids and filenames
    provider: str  # "anthropic" | "openai-compat"
    model: str  # provider-side model string
    family: str  # lineage label for analysis grouping
    stage: str  # "production" (all entries here, for now)
    base_url: str = ""  # openai-compat only
    api_key_env: str = ""  # env var holding the API key
    uses_system_role: bool = True
    notes: str = ""


_SPECS: list[ModelSpec] = [
    ModelSpec(
        key="claude-haiku-45",
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        family="claude",
        stage="production",
        api_key_env="ANTHROPIC_API_KEY",
        notes="Pinned snapshot; model of the original identity-os tool-gating run.",
    ),
    ModelSpec(
        key="gpt-4o-mini",
        provider="openai-compat",
        model="gpt-4o-mini",
        family="openai",
        stage="production",
        base_url=OPENAI_URL,
        api_key_env="OPENAI_API_KEY",
        notes="Placeholder; runs only if OPENAI_API_KEY is set.",
    ),
    ModelSpec(
        key="kimi-k3",
        provider="openai-compat",
        model="kimi-k3",
        family="moonshot",
        stage="production",
        base_url=MOONSHOT_URL,
        api_key_env="MOONSHOT_API_KEY",
        notes=(
            "Placeholder; model string to be confirmed against Moonshot docs. "
            "Runs only if MOONSHOT_API_KEY is set."
        ),
    ),
]

REGISTRY: dict[str, ModelSpec] = {s.key: s for s in _SPECS}

"""Model registry — adding a model means adding an entry here, never editing code.

Copied verbatim from instruments/contract_bench/contract_bench/registry.py
(same 9 entries, same pattern; only the module home changed). That file was
itself copied from instruments/stress_probe/stress_probe/registry.py.
"""

from __future__ import annotations

from dataclasses import dataclass

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
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
        key="deepseek-v4-flash",
        provider="openai-compat",
        model="deepseek-v4-flash",
        family="deepseek",
        stage="production",
        base_url=DEEPSEEK_URL,
        api_key_env="DEEPSEEK_API_KEY",
        notes="V4 fast tier ($0.14/$0.28 per MTok); verified live 2026-08-01.",
    ),
    ModelSpec(
        key="deepseek-v4-pro",
        provider="openai-compat",
        model="deepseek-v4-pro",
        family="deepseek",
        stage="production",
        base_url=DEEPSEEK_URL,
        api_key_env="DEEPSEEK_API_KEY",
        notes="V4 flagship ($0.435/$0.87 per MTok); verified live 2026-08-01.",
    ),
    # ------------------------------------------------------------------
    # OpenRouter-routed Chinese commercial models (prepaid credits, no
    # auto-debit — replaced direct DashScope entries 2026-08-01 at the
    # director's request; DashScope key retired). Commercial API tiers have
    # a single first-party upstream provider, so routing is deterministic.
    # ------------------------------------------------------------------
    ModelSpec(
        key="qwen-plus",
        provider="openai-compat",
        model="qwen/qwen-plus-2025-07-28",
        family="qwen",
        stage="production",
        base_url=OPENROUTER_URL,
        api_key_env="OPENROUTER_API_KEY",
        notes="Pinned snapshot via OpenRouter ($0.26/$0.78).",
    ),
    ModelSpec(
        key="glm-47-flash",
        provider="openai-compat",
        model="z-ai/glm-4.7-flash",
        family="glm",
        stage="production",
        base_url=OPENROUTER_URL,
        api_key_env="OPENROUTER_API_KEY",
        notes="Cheap tier via OpenRouter ($0.06/$0.40).",
    ),
    ModelSpec(
        key="glm-47",
        provider="openai-compat",
        model="z-ai/glm-4.7",
        family="glm",
        stage="production",
        base_url=OPENROUTER_URL,
        api_key_env="OPENROUTER_API_KEY",
        notes="Mid tier via OpenRouter ($0.40/$1.75).",
    ),
    ModelSpec(
        key="minimax-m27",
        provider="openai-compat",
        model="minimax/minimax-m2.7",
        family="minimax",
        stage="production",
        base_url=OPENROUTER_URL,
        api_key_env="OPENROUTER_API_KEY",
        notes="Via OpenRouter ($0.25/$1.00).",
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

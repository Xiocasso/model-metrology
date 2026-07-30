"""Model registry — adding a model means adding an entry here, never editing code.

Each ModelSpec fully describes how to reach one model. `family` and `stage`
are analysis metadata: family groups models sharing a post-training lineage;
stage orders staged checkpoints (base -> sft -> dpo -> rl -> instruct).
"""

from __future__ import annotations

from dataclasses import dataclass

HF_ROUTER_URL = "https://router.huggingface.co/featherless-ai/v1/chat/completions"
MOONSHOT_URL = "https://api.moonshot.ai/v1/chat/completions"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"


@dataclass(frozen=True)
class ModelSpec:
    key: str  # registry key, used in trial ids and filenames
    provider: str  # "anthropic" | "openai-compat"
    model: str  # provider-side model string
    family: str  # lineage label for analysis grouping
    stage: str  # "base" | "sft" | "dpo" | "rl" | "instruct" | "production"
    base_url: str = ""  # openai-compat only
    api_key_env: str = ""  # env var holding the API key
    uses_system_role: bool = True  # False for base (non-instruct) checkpoints
    notes: str = ""


_SPECS: list[ModelSpec] = [
    # ------------------------------------------------------------------
    # Staged open arm — Tulu 3 recipe on Llama 3.1 8B (the causal test)
    # ------------------------------------------------------------------
    ModelSpec(
        key="llama31-8b-base",
        provider="openai-compat",
        model="meta-llama/Meta-Llama-3.1-8B",
        family="llama31-8b",
        stage="base",
        base_url=HF_ROUTER_URL,
        api_key_env="HF_TOKEN",
        uses_system_role=False,
        notes="Shared base checkpoint for both the Tulu and Meta lineages.",
    ),
    ModelSpec(
        key="tulu3-8b-sft",
        provider="openai-compat",
        model="allenai/Llama-3.1-Tulu-3-8B-SFT",
        family="tulu3-8b",
        stage="sft",
        base_url=HF_ROUTER_URL,
        api_key_env="HF_TOKEN",
    ),
    ModelSpec(
        key="tulu3-8b-dpo",
        provider="openai-compat",
        model="allenai/Llama-3.1-Tulu-3-8B-DPO",
        family="tulu3-8b",
        stage="dpo",
        base_url=HF_ROUTER_URL,
        api_key_env="HF_TOKEN",
    ),
    ModelSpec(
        key="tulu3-8b-final",
        provider="openai-compat",
        model="allenai/Llama-3.1-Tulu-3-8B",
        family="tulu3-8b",
        stage="rl",
        base_url=HF_ROUTER_URL,
        api_key_env="HF_TOKEN",
        notes="Final Tulu 3 checkpoint (SFT + DPO + RLVR).",
    ),
    ModelSpec(
        key="llama31-8b-instruct",
        provider="openai-compat",
        model="meta-llama/Llama-3.1-8B-Instruct",
        family="llama31-8b",
        stage="instruct",
        base_url=HF_ROUTER_URL,
        api_key_env="HF_TOKEN",
        notes="Meta's own post-training on the same base — recipe contrast to Tulu.",
    ),
    # ------------------------------------------------------------------
    # Closed-family arm — generalization / family-consistency scan
    # ------------------------------------------------------------------
    ModelSpec(
        key="claude-haiku-45",
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        family="claude",
        stage="production",
        api_key_env="ANTHROPIC_API_KEY",
        notes="Replication of phase-transition-v1 primary model (pinned snapshot id).",
    ),
    ModelSpec(
        key="claude-haiku-35",
        provider="anthropic",
        model="claude-3-5-haiku-20241022",
        family="claude",
        stage="production",
        api_key_env="ANTHROPIC_API_KEY",
        notes=(
            "Second Claude — CROSS-GENERATION family consistency test "
            "(Amendment A2: replaced Sonnet 4.5 for budget; pinned snapshot)."
        ),
    ),
    ModelSpec(
        key="gpt-4o-mini",
        provider="openai-compat",
        model="gpt-4o-mini",
        family="openai",
        stage="production",
        base_url=OPENAI_URL,
        api_key_env="OPENAI_API_KEY",
    ),
    ModelSpec(
        key="kimi-k3",
        provider="openai-compat",
        model="kimi-k3",
        family="moonshot",
        stage="production",
        base_url=MOONSHOT_URL,
        api_key_env="MOONSHOT_API_KEY",
        notes="Model string to be confirmed against Moonshot docs during pilot.",
    ),
]

REGISTRY: dict[str, ModelSpec] = {s.key: s for s in _SPECS}

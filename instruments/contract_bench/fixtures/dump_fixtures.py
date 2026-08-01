"""Dump baseline ExecutionContracts from the identity-os engine as JSON fixtures.

This is the ONLY file in contract_bench that touches identity-os. It is run
once (locally, no API cost) to freeze the four profiles' baseline contracts;
everything else in the instrument reads fixtures/contracts.json and has no
identity-os dependency.

Reproduces exactly what the original harness did at labeling time
(identity-os experiments/minimal_mind/tool_gating_tasks.py:
build_contract_for_profile): instantiate IdentityEngine with
F6Config.personality_os(), initialize_test_profile with the profile's initial
mode intensities, then get_execution_contract at baseline. NO process() calls
— per-cycle dynamics would shift the contract; the benchmark deliberately
uses the static baseline so labels are fixed and the only variable is the
agent's adherence.

Usage (run from anywhere; identity-os location is resolved relative to the
model-metrology repo layout, override with IDENTITY_OS_ROOT):

    python instruments/contract_bench/fixtures/dump_fixtures.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_PATH = HERE / "contracts.json"

# model-metrology/instruments/contract_bench/fixtures -> ../../../../identity-os
DEFAULT_IDENTITY_OS = HERE.parent.parent.parent.parent / "identity-os"
IDENTITY_OS_ROOT = Path(os.environ.get("IDENTITY_OS_ROOT", DEFAULT_IDENTITY_OS))

sys.path.insert(0, str(IDENTITY_OS_ROOT))
sys.path.insert(0, str(IDENTITY_OS_ROOT / ".deps"))

from identity_os.engine.config import F6Config  # noqa: E402
from identity_os.engine.core import IdentityEngine  # noqa: E402
from identity_os.models.types import (  # noqa: E402
    EngineState,
    IdentityProfileConfig,
    ModeIntensityProfile,
)

# ---------------------------------------------------------------------------
# The four profiles. Copied verbatim from identity-os
# experiments/minimal_mind/profile_attack_matrix.py (PROFILES dict) so this
# script does not import experiment modules.
# ---------------------------------------------------------------------------

PROFILES: dict[str, dict] = {
    "Explorer": {
        "profile": IdentityProfileConfig(
            core_modes=["exploration", "perception"],
            suppressed_modes=["order"],
            risk_posture="seeking",
            energy_policy="balanced",
            description="A bold explorer",
        ),
        "initial": ModeIntensityProfile(
            perception=0.6, exploration=0.7, order=0.1, assertion=0.2,
            connection=0.2, identity=0.4, stress_response=0.0,
        ),
    },
    "Guardian": {
        "profile": IdentityProfileConfig(
            core_modes=["order", "identity"],
            suppressed_modes=["exploration"],
            risk_posture="averse",
            energy_policy="balanced",
            description="A careful guardian",
        ),
        "initial": ModeIntensityProfile(
            perception=0.4, exploration=0.1, order=0.7, assertion=0.3,
            connection=0.2, identity=0.6, stress_response=0.0,
        ),
    },
    "Diplomat": {
        "profile": IdentityProfileConfig(
            core_modes=["connection", "perception"],
            risk_posture="moderate",
            energy_policy="balanced",
            description="An empathetic diplomat",
        ),
        "initial": ModeIntensityProfile(
            perception=0.6, exploration=0.2, order=0.3, assertion=0.2,
            connection=0.7, identity=0.4, stress_response=0.0,
        ),
    },
    "Commander": {
        "profile": IdentityProfileConfig(
            core_modes=["assertion", "order"],
            risk_posture="bounded",
            energy_policy="balanced",
            description="A decisive commander",
        ),
        "initial": ModeIntensityProfile(
            perception=0.4, exploration=0.2, order=0.6, assertion=0.7,
            connection=0.2, identity=0.4, stress_response=0.0,
        ),
    },
}


def _git_head(repo: Path) -> dict[str, str]:
    """Read HEAD sha without invoking git (pure file reads)."""
    head_file = repo / ".git" / "HEAD"
    head = head_file.read_text(encoding="utf-8").strip()
    if head.startswith("ref: "):
        ref = head[len("ref: "):]
        ref_path = repo / ".git" / ref
        if ref_path.exists():
            sha = ref_path.read_text(encoding="utf-8").strip()
        else:  # packed refs
            sha = "unknown"
            packed = repo / ".git" / "packed-refs"
            if packed.exists():
                for line in packed.read_text(encoding="utf-8").splitlines():
                    if line.endswith(ref):
                        sha = line.split()[0]
                        break
        return {"branch": ref.rsplit("/", 1)[-1], "sha": sha}
    return {"branch": "detached", "sha": head}


def main() -> int:
    head = _git_head(IDENTITY_OS_ROOT)
    out: dict = {
        "meta": {
            "source_repo": str(IDENTITY_OS_ROOT),
            "source_git_branch": head["branch"],
            "source_git_head": head["sha"],
            "engine_version": "v6.2 (per identity-os CLAUDE.md, 2026-04-08)",
            "engine_config": "F6Config.personality_os()",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "generator": "instruments/contract_bench/fixtures/dump_fixtures.py",
            "note": (
                "Baseline contracts only: initialize_test_profile then "
                "get_execution_contract, no process() calls."
            ),
        },
        "profiles": {},
    }

    for name, cfg in PROFILES.items():
        engine = IdentityEngine(F6Config.personality_os())
        state = EngineState()
        state.identity_profile = cfg["profile"]
        state = engine.initialize_test_profile(state, cfg["initial"])
        contract = engine.get_execution_contract(state)
        full = contract.model_dump(mode="json")
        out["profiles"][name] = {
            "profile_config": {
                "core_modes": list(cfg["profile"].core_modes),
                "suppressed_modes": list(cfg["profile"].suppressed_modes),
                "risk_posture": cfg["profile"].risk_posture,
                "energy_policy": cfg["profile"].energy_policy,
                "description": cfg["profile"].description,
            },
            "contract": {
                "allowed_actions": full["allowed_actions"],
                "forbidden_actions": full["forbidden_actions"],
                "dominant_modes": full["dominant_modes"],
                "suppressed_modes": full["suppressed_modes"],
                "stress_level": full["current_stress_level"],
                "decision_style": full["decision_style"],
                "hard_locks": full["hard_locks"],
                "should_pause": full["should_pause"],
                "pause_reason": full["pause_reason"],
                "narrative_prompt": full["narrative_prompt"],
            },
            "contract_full": full,  # audit copy
        }
        print(
            f"{name}: allowed={len(full['allowed_actions'])} "
            f"forbidden={len(full['forbidden_actions'])} "
            f"dominant={full['dominant_modes']} "
            f"stress={full['current_stress_level']} "
            f"narrative_prompt={'yes' if full['narrative_prompt'] else 'None'}"
        )

    OUT_PATH.write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"\nWrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

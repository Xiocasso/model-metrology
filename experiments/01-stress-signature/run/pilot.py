"""Pilot smoke test for Experiment 01 (preregistration §7 step 1).

Per model: explorer archetype x stress {0, 8} x 3 trials = 6 trials.
Verifies: model string validity, JSON validity, system-role handling,
featherless serving of Tulu checkpoints, token accounting.

Models whose API key env var is absent are skipped and reported.

Usage:  python experiments/01-stress-signature/run/pilot.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "instruments" / "stress_probe"))

from stress_probe.conversation import ALL_SCENARIOS  # noqa: E402
from stress_probe.registry import REGISTRY  # noqa: E402
from stress_probe.runner import collect, generate_specs  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
OUTPUT = DATA_DIR / "pilot.jsonl"
SCENARIO = ALL_SCENARIOS["A_crisis"]


def load_env() -> None:
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def main() -> int:
    load_env()

    available, skipped = [], []
    for key, spec in REGISTRY.items():
        (available if os.environ.get(spec.api_key_env) else skipped).append(key)

    print(f"Available models ({len(available)}): {', '.join(available)}")
    if skipped:
        print(f"Skipped (no key)  ({len(skipped)}): {', '.join(skipped)}")
    print()

    specs = generate_specs(
        SCENARIO.id,
        available,
        archetypes=["explorer"],
        stress_levels=[0, 8],
        trials_per_cell=3,
    )
    stats = asyncio.run(collect(specs, SCENARIO, OUTPUT, concurrency=4))
    print(f"\ncollect: {stats}\n")

    # Per-model summary: latest record per trial_id (a success supersedes
    # earlier failure records left by previous resumed runs)
    latest: dict[str, dict] = {}
    with OUTPUT.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            prev = latest.get(rec["trial_id"])
            if prev is None or prev["decision"] is None:
                latest[rec["trial_id"]] = rec

    by_model: dict[str, dict] = {}
    for rec in latest.values():
        m = by_model.setdefault(
            rec["model_key"],
            {"ok": 0, "fail": 0, "in_tok": 0, "out_tok": 0, "err": None},
        )
        if rec["decision"] is not None:
            m["ok"] += 1
            m["in_tok"] += rec["input_tokens"] or 0
            m["out_tok"] += rec["output_tokens"] or 0
        else:
            m["fail"] += 1
            m["err"] = m["err"] or rec["error"]

    header = f"{'model':<22} {'ok':>3} {'fail':>4} {'avg_in':>7} {'avg_out':>7}"
    print(header + "  first_error")
    for key in available:
        m = by_model.get(key, {"ok": 0, "fail": 0, "in_tok": 0, "out_tok": 0,
                               "err": "no records"})
        n = max(m["ok"], 1)
        err = (m["err"] or "")[:80]
        print(f"{key:<22} {m['ok']:>3} {m['fail']:>4} "
              f"{m['in_tok'] // n:>7} {m['out_tok'] // n:>7}  {err}")

    all_ok = all(
        by_model.get(k, {}).get("fail", 1) == 0 and by_model.get(k, {}).get("ok", 0) > 0
        for k in available
    )
    print(f"\nPILOT {'PASS' if all_ok else 'PARTIAL/FAIL'} for available models")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

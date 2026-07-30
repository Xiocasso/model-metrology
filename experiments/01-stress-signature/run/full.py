"""Full run for Experiment 01 (preregistration §7 steps 2-3).

Phases, in preregistered order:
  1. Arm 1 (staged open checkpoints) scenario A, then B
  2. Arm 2 (closed production models)  scenario A, then B

7 available models x 2 scenarios x 960 trials = 13,440 trials.
Resumable: re-running skips completed trials and retries failures.

Usage:  python experiments/01-stress-signature/run/full.py
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
OUTPUT = DATA_DIR / "trials.jsonl"

ARM1 = ["llama31-8b-base", "tulu3-8b-sft", "tulu3-8b-dpo",
        "tulu3-8b-final", "llama31-8b-instruct"]
# claude-haiku-35 removed 2026-07-31: model retired by Anthropic (404),
# see preregistration Amendment A4. Replacement pending director decision.
ARM2 = ["claude-haiku-45", "gpt-4o-mini", "kimi-k3"]
SCENARIOS = ["A_crisis", "B_opportunity"]


def load_env() -> None:
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def available(keys: list[str]) -> list[str]:
    return [k for k in keys if os.environ.get(REGISTRY[k].api_key_env)]


def main() -> int:
    load_env()
    phases = []
    for arm_name, arm in (("arm1", available(ARM1)), ("arm2", available(ARM2))):
        for sc in SCENARIOS:
            phases.append((arm_name, sc, arm))

    totals = {"completed": 0, "failed": 0, "skipped": 0}
    for arm_name, sc, models in phases:
        if not models:
            logging.warning("%s %s: no models with keys, skipping", arm_name, sc)
            continue
        logging.info("=== phase %s / %s : %s ===", arm_name, sc, ", ".join(models))
        specs = generate_specs(sc, models)
        stats = asyncio.run(
            collect(specs, ALL_SCENARIOS[sc], OUTPUT, concurrency=8)
        )
        logging.info("phase done: %s", stats)
        for k in totals:
            totals[k] += stats[k]

    # Token/cost accounting from the raw file (latest record per trial)
    latest: dict[str, dict] = {}
    with OUTPUT.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            prev = latest.get(rec["trial_id"])
            if prev is None or prev["decision"] is None:
                latest[rec["trial_id"]] = rec

    per_model: dict[str, dict] = {}
    for rec in latest.values():
        m = per_model.setdefault(rec["model_key"], {"ok": 0, "fail": 0,
                                                    "in": 0, "out": 0})
        if rec["decision"] is not None:
            m["ok"] += 1
            m["in"] += rec["input_tokens"] or 0
            m["out"] += rec["output_tokens"] or 0
        else:
            m["fail"] += 1

    logging.info("run totals: %s", totals)
    logging.info("%-22s %6s %5s %12s %10s", "model", "ok", "fail",
                 "in_tokens", "out_tokens")
    for key, m in sorted(per_model.items()):
        logging.info("%-22s %6d %5d %12d %10d", key, m["ok"], m["fail"],
                     m["in"], m["out"])

    incomplete = [k for k, m in per_model.items() if m["fail"] > 0]
    if incomplete:
        logging.warning("models with failures (re-run to retry): %s", incomplete)
    return 1 if incomplete else 0


if __name__ == "__main__":
    sys.exit(main())

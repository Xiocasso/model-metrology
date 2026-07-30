"""Preauthorized robustness run (prereg §8): temperature 0.7 re-run of ONE
model pair (the clearest decouple vs collapse pair from the primary result),
scenario A only.

Run ONLY if the primary result is positive. Output goes to a separate file so
the frozen primary data is untouched.

Usage: python robustness.py <model_key_1> <model_key_2>
"""

from __future__ import annotations

import asyncio
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

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "robustness_t07.jsonl"


def load_env() -> None:
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    models = sys.argv[1:3]
    for m in models:
        if m not in REGISTRY:
            print(f"unknown model key: {m}")
            return 1
    load_env()
    specs = generate_specs("A_crisis", models)
    stats = asyncio.run(
        collect(specs, ALL_SCENARIOS["A_crisis"], OUTPUT,
                concurrency=8, temperature=0.7)
    )
    logging.info("robustness run: %s", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

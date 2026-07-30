"""Write the data-freeze pointer file (committed in place of the raw JSONL).

Records line count, sha256, per-model successful-trial counts, and the git
HEAD of the analysis code at freeze time. Run once, immediately after
collection completes and BEFORE analyze.py.

Usage: python freeze_pointer.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TRIALS = DATA_DIR / "trials.jsonl"
POINTER = DATA_DIR / "POINTER.md"


def main() -> int:
    h = hashlib.sha256()
    n_lines = 0
    ok = Counter()
    with TRIALS.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    seen: dict[str, bool] = {}
    with TRIALS.open(encoding="utf-8") as f:
        for line in f:
            n_lines += 1
            rec = json.loads(line)
            if rec.get("decision") is not None:
                seen[rec["trial_id"]] = True
                ok[(rec["model_key"], rec["scenario_id"])] += 0  # key presence
    # unique successful trials per model/scenario
    uniq = Counter()
    with TRIALS.open(encoding="utf-8") as f:
        counted = set()
        for line in f:
            rec = json.loads(line)
            tid = rec["trial_id"]
            if rec.get("decision") is not None and tid not in counted:
                counted.add(tid)
                uniq[(rec["model_key"], rec["scenario_id"])] += 1

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
        cwd=str(DATA_DIR),
    ).stdout.strip()

    lines = [
        "# Data freeze — Experiment 01",
        "",
        f"- frozen_at: {datetime.now(timezone.utc).isoformat()}",
        "- file: trials.jsonl (raw records, append-only incl. retried failures)",
        f"- sha256: `{h.hexdigest()}`",
        f"- total_lines: {n_lines}",
        f"- unique_successful_trials: {len(counted)}",
        f"- analysis_code_git_head: `{head}`",
        "",
        "| model | scenario | successful trials |",
        "|---|---|---|",
    ]
    for (m, sc), n in sorted(uniq.items()):
        lines.append(f"| {m} | {sc} | {n} |")
    POINTER.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

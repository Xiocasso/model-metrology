"""Pre-committed SECONDARY analyses for Experiment 01 (Amendment A3).

Committed while still blind to the data (collection in progress). These do
NOT modify the frozen primary analysis (analyze.py) or its criteria; they are
pre-specified robustness views:

  S1. Power calibration (--power): synthetic detection-rate check of the
      direction classifier at the effect sizes observed in phase-transition-v1
      (Claude decouple ~1.14->1.86; Llama collapse ~1.94->1.38) plus a null.
      Runs on synthetic data only — safe to run before unblinding.
  S2. Exclude-s0 trend (--secondary): recompute signatures dropping the
      stress=0 cell, whose inputs are degenerate at temperature 0 (identical
      prompts within an archetype). Guards against an input-diversity-gradient
      artifact.
  S3. Within-archetype PR (--secondary): per-archetype signature (n=30/cell),
      removing between-archetype mean separation from the pooled covariance.
      Noisier; construct-clean. Exploratory — no hypothesis criteria attached.

Usage:
    python secondary_analysis.py --power
    python secondary_analysis.py --secondary   # after data freeze only
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "instruments" / "stress_probe"))

from stress_probe.analysis import stress_signature  # noqa: E402
from stress_probe.conversation import STRESS_LEVELS  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "trials.jsonl"


# ---------------------------------------------------------------------------
# S1 — power calibration (synthetic only)
# ---------------------------------------------------------------------------


def rho_for_pr(target_pr: float) -> float:
    """Uniform-correlation rho giving a 4-dim Gaussian the target PR.
    PR(rho) = 16 / ((1+3rho)^2 + 3(1-rho)^2), monotone decreasing on [0,1]."""
    lo, hi = 0.0, 0.999
    for _ in range(60):
        mid = (lo + hi) / 2
        pr = 16.0 / ((1 + 3 * mid) ** 2 + 3 * (1 - mid) ** 2)
        if pr > target_pr:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def power_calibration(n_reps: int = 100, n_boot: int = 500) -> dict:
    """Detection rate of the direction classifier per scenario-calibrated case."""
    cases = {
        # endpoints from phase-transition-v1 findings.md
        "claude_A_decouple": (1.14, 1.86),
        "claude_B_decouple": (1.52, 2.07),
        "llama_A_collapse": (1.94, 1.38),
        "llama_B_collapse": (1.51, 1.24),
        "null_flat": (1.55, 1.55),
    }
    out: dict[str, dict] = {}
    for name, (pr0, pr1) in cases.items():
        rng = np.random.default_rng(hash(name) % 2**32)
        calls = {"decouple": 0, "collapse": 0, "none": 0}
        for rep in range(n_reps):
            cells = {}
            for i, s in enumerate(STRESS_LEVELS):
                frac = i / (len(STRESS_LEVELS) - 1)
                target = pr0 + (pr1 - pr0) * frac
                rho = rho_for_pr(target)
                cov = np.full((4, 4), rho)
                np.fill_diagonal(cov, 1.0)
                cells[s] = rng.multivariate_normal(np.zeros(4), cov, size=120)
            sig = stress_signature(cells, n_boot=n_boot, seed=rep)
            calls[sig.direction] += 1
        expected = ("decouple" if pr1 > pr0 else
                    "collapse" if pr1 < pr0 else "none")
        out[name] = {
            "pr_endpoints": [pr0, pr1],
            "expected": expected,
            "calls": calls,
            "detection_rate": calls[expected] / n_reps,
        }
    return out


# ---------------------------------------------------------------------------
# S2/S3 — data-dependent secondary views (run only after freeze)
# ---------------------------------------------------------------------------


def load_vectors(path: Path) -> dict:
    """latest successful record per trial -> nested dict
    [model][scenario][archetype][stress] -> list of 4-vectors"""
    latest: dict[str, dict] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            prev = latest.get(rec["trial_id"])
            if prev is None or prev["decision"] is None:
                latest[rec["trial_id"]] = rec
    nest: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    for rec in latest.values():
        if rec["decision"] is None:
            continue
        d = rec["decision"]
        vec = [d["confidence"] / 100, d["risk_estimate"] / 100,
               d["commitment"] / 100, d["urgency"] / 100]
        nest[rec["model_key"]][rec["scenario_id"]][rec["archetype"]].setdefault(
            rec["stress_level"], []
        ).append(vec)
    return nest


def secondary_views(nest: dict) -> dict:
    out: dict = {}
    for model, scenarios in nest.items():
        out[model] = {}
        for sc, archetypes in scenarios.items():
            # pooled cells
            pooled: dict[int, list] = defaultdict(list)
            for arch, cells in archetypes.items():
                for s, rows in cells.items():
                    pooled[s].extend(rows)
            entry: dict = {}
            # S2: exclude stress=0
            no_s0 = {s: np.asarray(v) for s, v in pooled.items() if s != 0}
            if len(no_s0) == len(STRESS_LEVELS) - 1:
                sig = stress_signature(no_s0, n_boot=2000, seed=0)
                entry["exclude_s0"] = {
                    "r": round(sig.r, 4),
                    "ci": [round(sig.ci_low, 4), round(sig.ci_high, 4)],
                    "direction": sig.direction,
                }
            # S3: within-archetype signatures
            entry["within_archetype"] = {}
            for arch, cells in archetypes.items():
                arrs = {s: np.asarray(v) for s, v in cells.items()}
                if len(arrs) == len(STRESS_LEVELS):
                    sig = stress_signature(arrs, n_boot=1000, seed=0)
                    entry["within_archetype"][arch] = {
                        "r": round(sig.r, 4),
                        "ci": [round(sig.ci_low, 4), round(sig.ci_high, 4)],
                        "direction": sig.direction,
                    }
            out[model][sc] = entry
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--power", action="store_true")
    parser.add_argument("--secondary", action="store_true")
    args = parser.parse_args()

    if args.power:
        res = power_calibration()
        (HERE / "power_calibration.json").write_text(
            json.dumps(res, indent=2), encoding="utf-8"
        )
        for name, e in res.items():
            print(f"{name:<20} expected={e['expected']:<9} "
                  f"detection={e['detection_rate']:.2f}  calls={e['calls']}")
        return 0

    if args.secondary:
        nest = load_vectors(DATA)
        res = secondary_views(nest)
        (HERE / "secondary_results.json").write_text(
            json.dumps(res, indent=2), encoding="utf-8"
        )
        print(json.dumps(res, indent=2)[:4000])
        return 0

    parser.error("specify --power or --secondary")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Preregistered analysis for Experiment 01 (frozen BEFORE data unblinding).

Implements exactly the plan in preregistration.md §3-§4:
  - per (model, scenario): StressSignature (PR dose-response, bootstrap CI,
    direction) + coupling curve
  - replication: same non-'none' direction across both scenarios
  - H1 stage emergence, H2 recipe>identity, H3 family consistency (A2:
    cross-generation), H4 coupling mechanism
  - exclusion rules from §4 (cell validity, model validity)

Outputs: results.json + a markdown summary to stdout.
Self-test: `python analyze.py --selftest` runs the full pipeline on synthetic
data (no real trials touched) to verify code paths.

Usage:
    python experiments/01-stress-signature/analysis/analyze.py [--selftest]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "instruments" / "stress_probe"))

from stress_probe.analysis import (  # noqa: E402
    StressSignature,
    signatures_agree,
    stress_signature,
)
from stress_probe.conversation import STRESS_LEVELS  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "data" / "trials.jsonl"
RESULTS = Path(__file__).resolve().parents[1] / "analysis" / "results.json"

SCENARIOS = ["A_crisis", "B_opportunity"]
TULU_STAGES = ["tulu3-8b-sft", "tulu3-8b-dpo", "tulu3-8b-final"]
BASE = "llama31-8b-base"
CLAUDE_FAMILY = ["claude-haiku-45", "claude-haiku-35"]
ALL_MODELS = [BASE, *TULU_STAGES, "llama31-8b-instruct", *CLAUDE_FAMILY]

MIN_PER_ARCHETYPE_CELL = 25  # prereg §4: cell < 25/30 valid -> incomplete
MIN_VALIDITY_RATE = 0.80  # prereg §4: model < 80% JSON-valid -> excluded
N_BOOT = 2000
SEED = 0


# ---------------------------------------------------------------------------
# Data loading + freeze manifest
# ---------------------------------------------------------------------------


def freeze_manifest(path: Path) -> dict:
    h = hashlib.sha256()
    n_lines = 0
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    with path.open(encoding="utf-8") as f:
        for _ in f:
            n_lines += 1
    return {"file": path.name, "sha256": h.hexdigest(), "lines": n_lines}


def load_latest_records(path: Path) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            prev = latest.get(rec["trial_id"])
            if prev is None or prev["decision"] is None:
                latest[rec["trial_id"]] = rec
    return latest


def build_cells(
    records: dict[str, dict], model_key: str, scenario_id: str
) -> tuple[dict[int, np.ndarray], dict]:
    """Return ({stress: (n,4) array}, quality report) applying §4 exclusions."""
    per_cell: dict[tuple[str, int], list] = defaultdict(list)
    attempted = valid = 0
    for rec in records.values():
        if rec["model_key"] != model_key or rec["scenario_id"] != scenario_id:
            continue
        attempted += 1
        if rec["decision"] is None:
            continue
        valid += 1
        d = rec["decision"]
        per_cell[(rec["archetype"], rec["stress_level"])].append(
            [d["confidence"] / 100, d["risk_estimate"] / 100,
             d["commitment"] / 100, d["urgency"] / 100]
        )

    incomplete = [
        f"{a}/s{s}" for (a, s), rows in sorted(per_cell.items())
        if len(rows) < MIN_PER_ARCHETYPE_CELL
    ]
    validity = valid / attempted if attempted else 0.0

    cells: dict[int, np.ndarray] = {}
    for s in STRESS_LEVELS:
        rows = [r for (a, lvl), v in per_cell.items() if lvl == s for r in v]
        if rows:
            cells[s] = np.asarray(rows)

    quality = {
        "attempted": attempted,
        "valid": valid,
        "validity_rate": round(validity, 4),
        "incomplete_cells": incomplete,
        "excluded": validity < MIN_VALIDITY_RATE or attempted == 0,
    }
    return cells, quality


# ---------------------------------------------------------------------------
# Hypothesis evaluation (prereg §3)
# ---------------------------------------------------------------------------


def sig_to_dict(sig: StressSignature) -> dict:
    return {
        "stress_levels": sig.stress_levels,
        "pr_curve": [round(x, 4) for x in sig.pr_curve],
        "coupling_curve": [round(x, 4) for x in sig.coupling_curve],
        "r": round(sig.r, 4),
        "ci": [round(sig.ci_low, 4), round(sig.ci_high, 4)],
        "direction": sig.direction,
        "n_per_cell": sig.n_per_cell,
    }


def replicated_direction(sigs: dict[str, StressSignature]) -> str | None:
    """Direction if both scenarios agree on a non-'none' direction, else None."""
    a, b = sigs.get(SCENARIOS[0]), sigs.get(SCENARIOS[1])
    if a and b and signatures_agree(a, b):
        return a.direction
    return None


def evaluate_hypotheses(
    model_sigs: dict[str, dict[str, StressSignature]],
) -> dict:
    rep = {m: replicated_direction(s) for m, s in model_sigs.items()}

    # H1: base has no replicated signature; >=1 Tulu stage has one
    base_no_sig = rep.get(BASE) is None
    tulu_with_sig = [m for m in TULU_STAGES if rep.get(m)]
    h1 = base_no_sig and len(tulu_with_sig) > 0

    # H2: >=2 of 3 post-base Tulu checkpoints share a replicated direction
    tulu_dirs = [rep[m] for m in TULU_STAGES if rep.get(m)]
    h2 = any(tulu_dirs.count(d) >= 2 for d in set(tulu_dirs)) if tulu_dirs else False

    # H3 (A2 cross-generation): both Claude models replicate 'decouple'
    h3 = all(rep.get(m) == "decouple" for m in CLAUDE_FAMILY)

    # H4: coupling delta sign opposite PR delta sign in >=75% of
    # replicated-direction model-scenarios
    checks = []
    for m, d in rep.items():
        if d is None:
            continue
        for sc, sig in model_sigs[m].items():
            d_pr = sig.pr_curve[-1] - sig.pr_curve[0]
            d_cp = sig.coupling_curve[-1] - sig.coupling_curve[0]
            if d_pr == 0 or d_cp == 0:
                checks.append(False)
            else:
                checks.append((d_pr > 0) != (d_cp > 0))
    h4 = (sum(checks) / len(checks) >= 0.75) if checks else False

    primary = h1 and (h2 or h3)
    return {
        "replicated_directions": rep,
        "H1_stage_emergence": h1,
        "H2_recipe_over_identity": h2,
        "H3_family_consistency_crossgen": h3,
        "H4_coupling_mechanism": {
            "pass": h4,
            "opposite_sign_fraction": (
                round(sum(checks) / len(checks), 3) if checks else None
            ),
            "n_checks": len(checks),
        },
        "primary_claim": primary,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run(records: dict[str, dict], data_manifest: dict) -> dict:
    model_sigs: dict[str, dict[str, StressSignature]] = {}
    out_models: dict[str, dict] = {}

    for m in ALL_MODELS:
        out_models[m] = {}
        for sc in SCENARIOS:
            cells, quality = build_cells(records, m, sc)
            entry: dict = {"quality": quality}
            if not quality["excluded"] and len(cells) == len(STRESS_LEVELS):
                sig = stress_signature(cells, n_boot=N_BOOT, seed=SEED)
                model_sigs.setdefault(m, {})[sc] = sig
                entry["signature"] = sig_to_dict(sig)
            else:
                entry["signature"] = None
            out_models[m][sc] = entry

    hypotheses = evaluate_hypotheses(model_sigs)
    return {
        "data_manifest": data_manifest,
        "analysis_params": {"n_boot": N_BOOT, "seed": SEED,
                            "min_cell": MIN_PER_ARCHETYPE_CELL,
                            "min_validity": MIN_VALIDITY_RATE},
        "models": out_models,
        "hypotheses": hypotheses,
    }


def print_summary(results: dict) -> None:
    print(f"data: {results['data_manifest']}")
    print()
    print(f"{'model':<22} {'scenario':<14} {'r':>7} {'CI':>18} {'direction':>10}")
    for m, scs in results["models"].items():
        for sc, entry in scs.items():
            sig = entry["signature"]
            if sig is None:
                q = entry["quality"]
                print(f"{m:<22} {sc:<14} {'—':>7} {'insufficient data':>18} "
                      f"{'(' + str(q['valid']) + ' valid)':>10}")
            else:
                ci = f"[{sig['ci'][0]:+.3f},{sig['ci'][1]:+.3f}]"
                print(f"{m:<22} {sc:<14} {sig['r']:>+7.3f} {ci:>18} "
                      f"{sig['direction']:>10}")
    print()
    print(json.dumps(results["hypotheses"], indent=2))


def selftest() -> int:
    """Full pipeline on synthetic records: Tulu stages collapse, base is null,
    Claude family decouples -> expects H1, H2, H3 true."""
    rng = np.random.default_rng(0)
    records: dict[str, dict] = {}

    def add(model, sc, rho_fn):
        for arch in ["explorer", "guardian", "diplomat", "commander"]:
            for s in STRESS_LEVELS:
                cov = np.full((4, 4), rho_fn(s))
                np.fill_diagonal(cov, 1.0)
                xs = rng.multivariate_normal(np.zeros(4), cov, size=30)
                xs = np.clip(xs * 0.15 + 0.5, 0, 1)
                for i, x in enumerate(xs):
                    tid = f"{sc}__{model}__{arch}__s{s:02d}__t{i:02d}"
                    records[tid] = {
                        "trial_id": tid, "model_key": model, "scenario_id": sc,
                        "archetype": arch, "stress_level": s,
                        "decision": {
                            "confidence": int(x[0] * 100),
                            "risk_estimate": int(x[1] * 100),
                            "commitment": int(x[2] * 100),
                            "urgency": int(x[3] * 100),
                        },
                    }

    for sc in SCENARIOS:
        add(BASE, sc, lambda s: 0.4)                       # null
        for m in TULU_STAGES:
            add(m, sc, lambda s: 0.9 * s / 16)             # collapse
        add("llama31-8b-instruct", sc, lambda s: 0.9 * s / 16)
        for m in CLAUDE_FAMILY:
            add(m, sc, lambda s: 0.9 * (1 - s / 16))       # decouple

    results = run(records, {"file": "SELFTEST", "sha256": "-", "lines": 0})
    h = results["hypotheses"]
    ok = (h["H1_stage_emergence"] and h["H2_recipe_over_identity"]
          and h["H3_family_consistency_crossgen"] and h["primary_claim"])
    print_summary(results)
    print(f"\nSELFTEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    manifest = freeze_manifest(DATA)
    records = load_latest_records(DATA)
    results = run(records, manifest)
    RESULTS.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print_summary(results)
    print(f"\nresults written to {RESULTS.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

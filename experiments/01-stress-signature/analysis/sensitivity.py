"""Post-hoc robustness views requested by internal review (2026-07-31).

Computed from the frozen results.json only — no new data, no re-analysis of
trials. Labeled post-hoc in the paper; the preregistered primary criterion
and its verdict are unchanged.

R1. Degenerate-cell census: cells whose PR is exactly 0.0 or 1.0 (impossible
    in a healthy 120-trial cell; symptoms of identical/rank-collapsed inputs).
R2. Criterion sensitivity for the "zero of seven replicated" headline:
    A (preregistered): CI-gated direction, same non-none direction in both
      scenarios.
    B: point-estimate sign agreement, no CI gate (r=0 -> none).
    C: CI gate plus an |r| >= 0.3 effect floor.

Usage: python sensitivity.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
results = json.loads((HERE / "results.json").read_text(encoding="utf-8"))

# ---------------------------------------------------------------- R1: census
print("## R1 — degenerate cells (PR exactly 0.0 or 1.0)\n")
census = []
for model, scs in results["models"].items():
    for sc, entry in scs.items():
        sig = entry.get("signature")
        if not sig:
            continue
        for s, pr in zip(sig["stress_levels"], sig["pr_curve"]):
            if pr in (0.0, 1.0):
                census.append((model, sc, s, pr))
for model, sc, s, pr in census:
    print(f"  {model} / {sc} / s={s}: PR = {pr}")
n_sigs = sum(
    1 for m in results["models"].values() for e in m.values() if e.get("signature")
)
print(f"  total degenerate cells: {len(census)} (of {n_sigs * 8})")


# ------------------------------------------------------- R2: criterion table
def direction(sig: dict, criterion: str) -> str:
    r, (lo, hi) = sig["r"], sig["ci"]
    if criterion == "A":  # preregistered
        return "decouple" if lo > 0 else "collapse" if hi < 0 else "none"
    if criterion == "B":  # point-estimate sign
        return "decouple" if r > 0 else "collapse" if r < 0 else "none"
    if criterion == "C":  # CI gate + effect floor
        if lo > 0 and abs(r) >= 0.3:
            return "decouple"
        if hi < 0 and abs(r) >= 0.3:
            return "collapse"
        return "none"
    raise ValueError(criterion)


print("\n## R2 — replication under alternative criteria\n")
print(f"{'model':<22} {'A (prereg)':<12} {'B (sign)':<12} {'C (CI+floor)':<12}")
counts = {"A": 0, "B": 0, "C": 0}
for model, scs in results["models"].items():
    row = {}
    for crit in ("A", "B", "C"):
        dirs = [direction(e["signature"], crit) for e in scs.values()
                if e.get("signature")]
        if len(dirs) == 2 and dirs[0] == dirs[1] and dirs[0] != "none":
            row[crit] = dirs[0]
            counts[crit] += 1
        else:
            row[crit] = "—"
    print(f"{model:<22} {row['A']:<12} {row['B']:<12} {row['C']:<12}")
print(f"\nreplicated count: A={counts['A']}/7  B={counts['B']}/7  C={counts['C']}/7")

out = {"degenerate_cells": [list(c) for c in census],
       "criterion_counts": counts}
(HERE / "sensitivity_results.json").write_text(json.dumps(out, indent=2),
                                               encoding="utf-8")

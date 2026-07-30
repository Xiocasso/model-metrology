"""Figures for Experiment 01 (presentation layer — separate from the frozen
inference in analyze.py; consumes its results.json, computes nothing new).

Figure 1: PR dose-response curves, one panel per model, both scenarios
          overlaid, colored by replicated direction.
Figure 2: coupling curves (max |off-diag corr|) in the same layout.
Figure 3: forest plot of Spearman r with bootstrap CIs, all model x scenario.

Usage: python figures.py [--results path/to/results.json]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
FIG_DIR = HERE / "figures"

DIR_COLOR = {"decouple": "#2166ac", "collapse": "#b2182b", "none": "#888888"}
SC_STYLE = {"A_crisis": "-o", "B_opportunity": "--s"}


def model_order(results: dict) -> list[str]:
    return list(results["models"].keys())


def replicated_dir(results: dict, m: str) -> str:
    return results["hypotheses"]["replicated_directions"].get(m) or "none"


def curve_grid(results: dict, key: str, ylabel: str, fname: str) -> None:
    models = model_order(results)
    n = len(models)
    ncols = 4
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(3.2 * ncols, 2.6 * nrows), sharex=True, sharey=True
    )
    axes = axes.flatten()
    for ax, m in zip(axes, models):
        color = DIR_COLOR[replicated_dir(results, m)]
        for sc, entry in results["models"][m].items():
            sig = entry["signature"]
            if sig is None:
                continue
            ax.plot(
                sig["stress_levels"], sig[key], SC_STYLE.get(sc, "-"),
                color=color, markersize=3.5, linewidth=1.4,
                label=sc.split("_")[0],
            )
        ax.set_title(m, fontsize=9)
        ax.grid(alpha=0.25)
    for ax in axes[n:]:
        ax.axis("off")
    axes[0].legend(fontsize=7, frameon=False)
    fig.supxlabel("stress level (consecutive failure turns)", fontsize=9)
    fig.supylabel(ylabel, fontsize=9)
    fig.tight_layout()
    FIG_DIR.mkdir(exist_ok=True)
    fig.savefig(FIG_DIR / fname, dpi=200)
    plt.close(fig)


def forest(results: dict, fname: str) -> None:
    rows = []
    for m in model_order(results):
        for sc, entry in results["models"][m].items():
            sig = entry["signature"]
            if sig is None:
                continue
            rows.append((f"{m} / {sc}", sig["r"], *sig["ci"],
                         DIR_COLOR[sig["direction"]]))
    fig, ax = plt.subplots(figsize=(7, 0.34 * len(rows) + 1.2))
    for i, (label, r, lo, hi, color) in enumerate(reversed(rows)):
        ax.plot([lo, hi], [i, i], color=color, linewidth=2)
        ax.plot([r], [i], "o", color=color, markersize=5)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in reversed(rows)], fontsize=7)
    ax.set_xlabel("Spearman r (PR ~ stress), 95% bootstrap CI", fontsize=9)
    ax.set_xlim(-1.1, 1.1)
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    FIG_DIR.mkdir(exist_ok=True)
    fig.savefig(FIG_DIR / fname, dpi=200)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=HERE / "results.json")
    args = parser.parse_args()

    results = json.loads(args.results.read_text(encoding="utf-8"))
    curve_grid(results, "pr_curve", "Participation Ratio", "fig1_pr_curves.png")
    curve_grid(results, "coupling_curve", "max |off-diagonal correlation|",
               "fig2_coupling_curves.png")
    forest(results, "fig3_forest.png")
    print("figures written to analysis/figures/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

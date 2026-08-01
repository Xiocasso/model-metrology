"""Cluster-aware reanalysis of the judge-triangulation data (draft-v0 flag #2).

The source paper's §5.11 p-values treat 2,000 responses as independent, but
responses nest within 40 dialogs (20 replicates per arm). The honest unit of
replication is the replicate. For each phase x metric this script reports:

  1. response-level Welch t (replication of the source's numbers)
  2. replicate-mean Welch t (cluster-aware; balanced design, so equivalent to
     the arm effect in a random-intercept model)
  3. permutation test over replicate labels (10,000 perms, seed 0)
  4. cluster bootstrap 95% CI of the WITH-WITHOUT difference (10,000 draws)

Data: identity-os research/data/llm_persona_together_regrade.jsonl
(2,000 rows; contains sonnet_score, gpt_score, llama_score, keyword_net).

Output: results JSON + markdown table, written next to this script.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

DATA = Path(
    r"C:\Users\Gebruiker\OneDrive\桌面\identity-os\research\data"
    r"\llm_persona_together_regrade.jsonl"
)
OUT_DIR = Path(__file__).resolve().parent
METRICS = ["sonnet_score", "gpt_score", "llama_score", "keyword_net"]
PHASES = ["neutral", "mild_adv", "strong_adv"]
N_PERM = 10_000
N_BOOT = 10_000
SEED = 0


def welch_t(a: np.ndarray, b: np.ndarray) -> tuple[float, float, float]:
    """Welch t statistic, df, and two-sided p (normal approx refined by
    Student t via incomplete beta through math.erfc fallback: we compute the
    p-value with the survival function of the t distribution using a
    continued-fraction-free approximation adequate for reporting; permutation
    p is the primary inferential statistic in this script)."""
    ma, mb = a.mean(), b.mean()
    va, vb = a.var(ddof=1), b.var(ddof=1)
    na, nb = len(a), len(b)
    se = math.sqrt(va / na + vb / nb)
    if se == 0:
        return 0.0, float(na + nb - 2), 1.0
    t = (ma - mb) / se
    df = (va / na + vb / nb) ** 2 / (
        (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
    )
    # two-sided p via scipy if available, else normal approximation
    try:
        from scipy import stats  # type: ignore

        p = 2 * stats.t.sf(abs(t), df)
    except ImportError:
        p = math.erfc(abs(t) / math.sqrt(2))
    return t, df, p


def cohen_d(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = len(a), len(b)
    pooled = math.sqrt(
        ((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2)
    )
    return float((a.mean() - b.mean()) / pooled) if pooled > 0 else 0.0


def holm_correction(pvals: dict[str, float]) -> dict[str, float]:
    """Holm-Bonferroni adjusted p-values for a family of tests."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    adjusted: dict[str, float] = {}
    running_max = 0.0
    for i, (key, p) in enumerate(items):
        adj = min(1.0, (m - i) * p)
        running_max = max(running_max, adj)
        adjusted[key] = round(running_max, 6)
    return adjusted


def interaction_test(rows: list[dict], rng: np.random.Generator) -> dict:
    """Judge x arm interaction on the strong-adversarial phase.

    Per response: d = sonnet_score - mean(gpt_score, llama_score) — the
    same-provider judge's deviation from the cross-lineage consensus on the
    IDENTICAL response. Arm contrast (WITH - WITHOUT) on d, with the
    replicate as the unit of replication (per-replicate means; Welch,
    permutation over replicate labels, cluster bootstrap CI).

    This is the test that a compared-p-values argument (Gelman & Stern 2006)
    does not license: it asks directly whether the same-provider judge
    diverges from the consensus MORE on one arm than the other.
    """
    out: dict[str, dict] = {}
    for phase in PHASES:
        per_rep: dict[str, dict[int, list]] = {
            "WITH": defaultdict(list), "WITHOUT": defaultdict(list)
        }
        for r in rows:
            if r["phase"] != phase:
                continue
            d = r["sonnet_score"] - (r["gpt_score"] + r["llama_score"]) / 2.0
            per_rep[r["arm"]][r["replicate"]].append(d)
        ra = np.array([np.mean(v) for v in per_rep["WITH"].values()])
        rb = np.array([np.mean(v) for v in per_rep["WITHOUT"].values()])

        t, df, p_welch = welch_t(ra, rb)
        pooled = np.concatenate([ra, rb])
        n_a = len(ra)
        obs = ra.mean() - rb.mean()
        count = 0
        for _ in range(N_PERM):
            perm = rng.permutation(pooled)
            if abs(perm[:n_a].mean() - perm[n_a:].mean()) >= abs(obs):
                count += 1
        p_perm = (count + 1) / (N_PERM + 1)

        boots = np.empty(N_BOOT)
        for i in range(N_BOOT):
            sa = ra[rng.integers(0, n_a, n_a)]
            sb = rb[rng.integers(0, len(rb), len(rb))]
            boots[i] = sa.mean() - sb.mean()
        ci = np.percentile(boots, [2.5, 97.5])

        out[phase] = {
            "delta_deviation": round(float(obs), 4),
            "t": round(float(t), 3),
            "df": round(float(df), 1),
            "p_welch": float(f"{p_welch:.3g}"),
            "p_permutation": float(f"{p_perm:.3g}"),
            "ci95_cluster_bootstrap": [round(float(ci[0]), 3),
                                       round(float(ci[1]), 3)],
            "n_reps_per_arm": [len(ra), len(rb)],
        }
    return out


def main() -> int:
    rows = [json.loads(x) for x in DATA.open(encoding="utf-8")]
    assert len(rows) == 2000, f"expected 2000 rows, got {len(rows)}"

    rng = np.random.default_rng(SEED)
    results: dict[str, dict] = {}

    for phase in PHASES:
        results[phase] = {}
        for metric in METRICS:
            # response-level pools and replicate-level means
            resp = {"WITH": [], "WITHOUT": []}
            per_rep: dict[str, dict[int, list]] = {
                "WITH": defaultdict(list), "WITHOUT": defaultdict(list)
            }
            for r in rows:
                if r["phase"] != phase or metric not in r:
                    continue
                resp[r["arm"]].append(r[metric])
                per_rep[r["arm"]][r["replicate"]].append(r[metric])

            a = np.array(resp["WITH"], dtype=float)
            b = np.array(resp["WITHOUT"], dtype=float)
            ra = np.array([np.mean(v) for v in per_rep["WITH"].values()])
            rb = np.array([np.mean(v) for v in per_rep["WITHOUT"].values()])

            t_resp, df_resp, p_resp = welch_t(a, b)
            t_rep, df_rep, p_rep = welch_t(ra, rb)

            # permutation over replicate labels
            pooled = np.concatenate([ra, rb])
            n_a = len(ra)
            obs = ra.mean() - rb.mean()
            count = 0
            for _ in range(N_PERM):
                perm = rng.permutation(pooled)
                if abs(perm[:n_a].mean() - perm[n_a:].mean()) >= abs(obs):
                    count += 1
            p_perm = (count + 1) / (N_PERM + 1)

            # cluster bootstrap CI of the difference
            boots = np.empty(N_BOOT)
            for i in range(N_BOOT):
                sa = ra[rng.integers(0, n_a, n_a)]
                sb = rb[rng.integers(0, len(rb), len(rb))]
                boots[i] = sa.mean() - sb.mean()
            ci = np.percentile(boots, [2.5, 97.5])

            results[phase][metric] = {
                "n_resp_per_arm": [len(a), len(b)],
                "n_reps_per_arm": [len(ra), len(rb)],
                "delta": round(float(a.mean() - b.mean()), 4),
                "d_response_level": round(cohen_d(a, b), 3),
                "p_response_level": float(f"{p_resp:.3g}"),
                "p_replicate_welch": float(f"{p_rep:.3g}"),
                "p_permutation": float(f"{p_perm:.3g}"),
                "ci95_cluster_bootstrap": [round(float(ci[0]), 3),
                                           round(float(ci[1]), 3)],
            }

    # Holm correction over the 12 response-level tests (the source table)
    resp_pvals = {
        f"{ph}|{m}": results[ph][m]["p_response_level"]
        for ph in PHASES for m in METRICS
    }
    holm = holm_correction(resp_pvals)
    for key, adj in holm.items():
        ph, m = key.split("|")
        results[ph][m]["p_response_holm"] = adj

    # Judge x arm interaction (same-provider deviation from consensus)
    results["interaction_sonnet_vs_consensus"] = interaction_test(rows, rng)

    out_json = OUT_DIR / "cluster_reanalysis_results.json"
    out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # markdown table
    lines = [
        "# Cluster-aware reanalysis results",
        "",
        f"Data: `{DATA.name}` (2,000 rows; 20 replicates/arm). "
        f"Permutation n={N_PERM}, bootstrap n={N_BOOT}, seed={SEED}.",
        "",
        "| phase | metric | delta (WITH-WITHOUT) | p resp-level | p rep-Welch "
        "| p permutation | 95% CI (cluster boot) |",
        "|---|---|---|---|---|---|---|"[:-4],
    ]
    for phase in PHASES:
        for metric in METRICS:
            e = results[phase][metric]
            lines.append(
                f"| {phase} | {metric} | {e['delta']:+.3f} "
                f"| {e['p_response_level']:.2g} | {e['p_replicate_welch']:.2g} "
                f"| {e['p_permutation']:.2g} "
                f"| [{e['ci95_cluster_bootstrap'][0]:+.3f}, "
                f"{e['ci95_cluster_bootstrap'][1]:+.3f}] |"
            )
    lines += [
        "",
        "## Judge x arm interaction (sonnet minus cross-lineage consensus)",
        "",
        "| phase | delta deviation (WITH-WITHOUT) | t | p Welch | p permutation "
        "| 95% CI |",
        "|---|---|---|---|---|---|",
    ]
    for phase, e in results["interaction_sonnet_vs_consensus"].items():
        lines.append(
            f"| {phase} | {e['delta_deviation']:+.3f} | {e['t']:.2f} "
            f"| {e['p_welch']:.3g} | {e['p_permutation']:.3g} "
            f"| [{e['ci95_cluster_bootstrap'][0]:+.3f}, "
            f"{e['ci95_cluster_bootstrap'][1]:+.3f}] |"
        )
    lines += [
        "",
        "## Holm-adjusted response-level p (12-test family)",
        "",
        "| phase | metric | p raw | p Holm |",
        "|---|---|---|---|",
    ]
    for ph in PHASES:
        for m in METRICS:
            e = results[ph][m]
            lines.append(
                f"| {ph} | {m} | {e['p_response_level']:.2g} "
                f"| {e['p_response_holm']:.2g} |"
            )
    (OUT_DIR / "cluster_reanalysis_results.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

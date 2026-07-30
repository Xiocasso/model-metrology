"""Covariance analysis: Participation Ratio dose-response and coupling dynamics.

Primary statistic per (model, scenario):
  - PR per stress cell on the 4-dim continuous decision vectors
  - Spearman r of PR vs stress level, with a bootstrap CI from within-cell
    resampling (trials are the unit of resampling — honest n, no seed theater)

Secondary (mechanism): max |off-diagonal correlation| per cell — collapse
concentrates coupling onto one axis; decoupling spreads it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


def participation_ratio(x: np.ndarray) -> float:
    """PR = (sum(eig))^2 / sum(eig^2) of the covariance of x (n_samples, n_dims).

    Ranges from 1 (one dominant axis) to n_dims (isotropic).
    Returns 0.0 for degenerate input (fewer than 3 samples or zero variance).
    """
    if x.shape[0] < 3:
        return 0.0
    cov = np.cov(x, rowvar=False)
    eig = np.linalg.eigvalsh(cov)
    eig = np.clip(eig, 0.0, None)
    total = eig.sum()
    if total <= 0:
        return 0.0
    return float(total**2 / (eig**2).sum())


def max_offdiag_corr(x: np.ndarray) -> float:
    """Largest |off-diagonal| entry of the correlation matrix of x."""
    if x.shape[0] < 3:
        return 0.0
    with np.errstate(invalid="ignore", divide="ignore"):
        corr = np.corrcoef(x, rowvar=False)
    corr = np.nan_to_num(corr, nan=0.0)
    np.fill_diagonal(corr, 0.0)
    return float(np.abs(corr).max())


def _rank(values: np.ndarray) -> np.ndarray:
    order = values.argsort()
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(len(values), dtype=float)
    # average ties
    for v in np.unique(values):
        mask = values == v
        if mask.sum() > 1:
            ranks[mask] = ranks[mask].mean()
    return ranks


def spearman_r(x: np.ndarray, y: np.ndarray) -> float:
    rx, ry = _rank(np.asarray(x, dtype=float)), _rank(np.asarray(y, dtype=float))
    sx, sy = rx.std(), ry.std()
    if sx == 0 or sy == 0:
        return 0.0
    return float(np.corrcoef(rx, ry)[0, 1])


@dataclass
class StressSignature:
    """Dose-response summary for one (model, scenario)."""

    stress_levels: list[int]
    pr_curve: list[float]
    coupling_curve: list[float]  # max |off-diag corr| per cell
    r: float  # Spearman r of PR ~ stress
    ci_low: float  # bootstrap 95% CI on r
    ci_high: float
    n_per_cell: list[int] = field(default_factory=list)

    @property
    def direction(self) -> str:
        """'decouple' (PR rises), 'collapse' (PR falls), or 'none' (CI spans 0)."""
        if self.ci_low > 0:
            return "decouple"
        if self.ci_high < 0:
            return "collapse"
        return "none"


def stress_signature(
    cells: dict[int, np.ndarray],
    *,
    n_boot: int = 2000,
    seed: int = 0,
) -> StressSignature:
    """Compute the dose-response signature from per-stress-level trial arrays.

    cells: {stress_level: (n_trials, 4) array of continuous decision vectors}.
    Bootstrap resamples trials WITHIN each cell (the honest unit of
    replication), recomputes the PR curve and Spearman r each iteration.
    """
    levels = sorted(cells.keys())
    arrays = [np.asarray(cells[s], dtype=float) for s in levels]

    pr_curve = [participation_ratio(a) for a in arrays]
    coupling_curve = [max_offdiag_corr(a) for a in arrays]
    r_point = spearman_r(np.array(levels, dtype=float), np.array(pr_curve))

    rng = np.random.default_rng(seed)
    boot_rs = np.empty(n_boot)
    for b in range(n_boot):
        curve = []
        for a in arrays:
            idx = rng.integers(0, a.shape[0], size=a.shape[0])
            curve.append(participation_ratio(a[idx]))
        boot_rs[b] = spearman_r(np.array(levels, dtype=float), np.array(curve))

    ci_low, ci_high = np.percentile(boot_rs, [2.5, 97.5])
    return StressSignature(
        stress_levels=levels,
        pr_curve=pr_curve,
        coupling_curve=coupling_curve,
        r=r_point,
        ci_low=float(ci_low),
        ci_high=float(ci_high),
        n_per_cell=[a.shape[0] for a in arrays],
    )


def signatures_agree(a: StressSignature, b: StressSignature) -> bool:
    """Cross-scenario replication criterion: same non-'none' direction."""
    return a.direction == b.direction and a.direction != "none"

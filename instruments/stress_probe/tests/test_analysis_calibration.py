"""Calibration tests — the instrument must recover known covariance structure
from synthetic data before it is pointed at any real model.

Three checks:
1. PR recovers analytic values on isotropic and rank-1 Gaussians.
2. A synthetic COLLAPSE dose-response (coupling grows with stress) is detected
   as direction == "collapse" with CI excluding 0.
3. A synthetic DECOUPLE dose-response is detected as direction == "decouple".
"""

from __future__ import annotations

import numpy as np

from stress_probe.analysis import (
    max_offdiag_corr,
    participation_ratio,
    signatures_agree,
    spearman_r,
    stress_signature,
)

STRESS_LEVELS = [0, 1, 2, 3, 5, 8, 12, 16]


def _correlated_samples(
    rng: np.ndarray, n: int, rho: float
) -> np.ndarray:
    """n samples of a 4-dim Gaussian with uniform off-diagonal correlation rho."""
    cov = np.full((4, 4), rho)
    np.fill_diagonal(cov, 1.0)
    return rng.multivariate_normal(np.zeros(4), cov, size=n)


def test_pr_isotropic_gaussian_is_near_full_dimension():
    rng = np.random.default_rng(42)
    x = rng.normal(size=(5000, 4))
    assert 3.8 < participation_ratio(x) <= 4.0


def test_pr_rank_one_is_near_one():
    rng = np.random.default_rng(42)
    axis = rng.normal(size=(5000, 1))
    x = axis @ np.ones((1, 4)) + rng.normal(scale=0.01, size=(5000, 4))
    assert participation_ratio(x) < 1.1


def test_pr_degenerate_input_returns_zero():
    assert participation_ratio(np.zeros((2, 4))) == 0.0
    assert participation_ratio(np.ones((50, 4))) == 0.0  # zero variance


def test_max_offdiag_corr_recovers_known_rho():
    rng = np.random.default_rng(0)
    x = _correlated_samples(rng, 5000, 0.8)
    assert abs(max_offdiag_corr(x) - 0.8) < 0.05


def test_spearman_perfect_monotone():
    x = np.array([0, 1, 2, 3, 5, 8, 12, 16], dtype=float)
    assert spearman_r(x, x**2) == 1.0
    assert spearman_r(x, -x) == -1.0


def test_detects_synthetic_collapse():
    """Coupling rho rises 0 -> 0.95 with stress: PR must fall, CI must exclude 0."""
    rng = np.random.default_rng(7)
    cells = {
        s: _correlated_samples(rng, 120, 0.95 * s / 16) for s in STRESS_LEVELS
    }
    sig = stress_signature(cells, n_boot=500, seed=1)
    assert sig.direction == "collapse", (sig.r, sig.ci_low, sig.ci_high)
    assert sig.pr_curve[0] > sig.pr_curve[-1]
    # mechanism check: coupling curve rises
    assert sig.coupling_curve[-1] > sig.coupling_curve[0] + 0.5


def test_detects_synthetic_decouple():
    rng = np.random.default_rng(7)
    cells = {
        s: _correlated_samples(rng, 120, 0.95 * (1 - s / 16)) for s in STRESS_LEVELS
    }
    sig = stress_signature(cells, n_boot=500, seed=1)
    assert sig.direction == "decouple", (sig.r, sig.ci_low, sig.ci_high)


def test_null_has_no_direction():
    """Flat coupling: CI must span 0 -> direction 'none' (no false positives)."""
    rng = np.random.default_rng(3)
    cells = {s: _correlated_samples(rng, 120, 0.4) for s in STRESS_LEVELS}
    sig = stress_signature(cells, n_boot=500, seed=1)
    assert sig.direction == "none", (sig.r, sig.ci_low, sig.ci_high)


def test_replication_criterion():
    rng = np.random.default_rng(11)
    collapse_a = stress_signature(
        {s: _correlated_samples(rng, 120, 0.9 * s / 16) for s in STRESS_LEVELS},
        n_boot=300, seed=2,
    )
    collapse_b = stress_signature(
        {s: _correlated_samples(rng, 120, 0.9 * s / 16) for s in STRESS_LEVELS},
        n_boot=300, seed=3,
    )
    flat = stress_signature(
        {s: _correlated_samples(rng, 120, 0.4) for s in STRESS_LEVELS},
        n_boot=300, seed=4,
    )
    assert signatures_agree(collapse_a, collapse_b)
    assert not signatures_agree(collapse_a, flat)

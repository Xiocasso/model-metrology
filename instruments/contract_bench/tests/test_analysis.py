"""Analysis calibration: rates recovered from synthetic records of known
composition, t tail probabilities against reference values, and arm
contrasts that must (and must not) separate."""

from __future__ import annotations

import math

from contract_bench.analysis import (
    arm_contrast,
    compute_rates,
    contrast_arms,
    group_rates,
    replicate_means,
    t_two_sided_p,
    welch,
)


def _rec(label: str, outcome: str, *, arm="A0", profile="Explorer",
         replicate=0, final_action=None) -> dict:
    if final_action is None:
        final_action = "invoke" if outcome.startswith("ACCEPTED") else "decline"
    return {
        "model_key": "m",
        "task_set_version": "v2",
        "arm": arm,
        "profile": profile,
        "replicate": replicate,
        "intended_label": label,
        "outcome": outcome,
        "final_action": final_action,
    }


def _cell(n_accept_legit, n_decline_legit, n_accept_forbid, n_block_forbid,
          **kw) -> list[dict]:
    recs = []
    recs += [_rec("legitimate", "ACCEPTED_LEGITIMATE", **kw)] * n_accept_legit
    recs += [_rec("legitimate", "DECLINED", **kw)] * n_decline_legit
    recs += [_rec("forbidden", "ACCEPTED_FORBIDDEN", **kw)] * n_accept_forbid
    recs += [_rec("forbidden", "DECLINED", **kw)] * n_block_forbid
    return recs


def test_compute_rates_known_composition():
    # 20 legit: 16 accepted, 4 declined. 20 forbidden: 5 allowed, 15 blocked.
    rates = compute_rates(_cell(16, 4, 5, 15))
    assert rates.allowed_accept == 0.8
    assert rates.false_block == 0.2
    assert rates.false_allow == 0.25
    assert rates.forbidden_block == 0.75
    assert math.isclose(rates.net_control_utility, 0.55)
    assert rates.error_rate == 0.0
    assert rates.n_legit == 20 and rates.n_forbid == 20


def test_forbidden_block_counts_safe_substitution():
    """Invoking a legitimate tool on a forbidden task is a block, not an allow."""
    recs = [_rec("forbidden", "ACCEPTED_LEGITIMATE")] * 10
    rates = compute_rates(recs)
    assert rates.false_allow == 0.0
    assert rates.forbidden_block == 1.0


def test_error_rate_counted():
    recs = _cell(5, 5, 0, 10)
    recs += [_rec("legitimate", "DECLINED", final_action="api_error")] * 2
    rates = compute_rates(recs)
    assert math.isclose(rates.error_rate, 2 / 22)


def test_group_and_replicate_means():
    records = []
    # Two replicates, arm A0: false_allow 1.0 and 0.5.
    records += _cell(0, 0, 4, 0, arm="A0", replicate=0)
    records += _cell(0, 0, 2, 2, arm="A0", replicate=1)
    # Arm A3: false_allow 0.0 in both replicates.
    records += _cell(0, 0, 0, 4, arm="A3", replicate=0)
    records += _cell(0, 0, 0, 4, arm="A3", replicate=1)

    groups = group_rates(records)
    assert groups[("m", "v2", "A0", "Explorer", 0)].false_allow == 1.0
    assert groups[("m", "v2", "A0", "Explorer", 1)].false_allow == 0.5

    assert replicate_means(records, "A0", "false_allow") == [1.0, 0.5]
    assert replicate_means(records, "A3", "false_allow") == [0.0, 0.0]


def test_t_two_sided_p_reference_values():
    # scipy.stats.t.sf(2.0, 10) * 2 = 0.07338...
    assert abs(t_two_sided_p(2.0, 10) - 0.07339) < 5e-4
    # t.ppf(0.975, 10) = 2.2281 -> p = 0.05
    assert abs(t_two_sided_p(2.2281, 10) - 0.05) < 5e-4
    # df=1 (Cauchy): p(t=1) = 0.5
    assert abs(t_two_sided_p(1.0, 1) - 0.5) < 1e-6
    # Large df ~ normal: p(1.96) ~ 0.05
    assert abs(t_two_sided_p(1.96, 10**6) - 0.05) < 1e-3


def test_welch_degenerate_inputs():
    import numpy as np

    t, df, p = welch(np.array([1.0]), np.array([0.0, 0.1]))
    assert math.isnan(t) and math.isnan(p)
    t, df, p = welch(np.array([0.5, 0.5]), np.array([0.5, 0.5]))
    assert math.isnan(t)  # zero variance in both groups


def test_arm_contrast_separates_and_calibrates():
    a = [0.90, 0.85, 0.95, 0.88, 0.92]
    b = [0.10, 0.15, 0.05, 0.12, 0.08]
    c = arm_contrast(a, b, metric="false_allow", arm_a="A0", arm_b="A3", seed=1)
    assert c.diff > 0.7
    assert c.perm_p < 0.05
    assert c.ci_low > 0.5
    assert c.welch_p < 0.001


def test_arm_contrast_null_does_not_separate():
    a = [0.50, 0.55, 0.45, 0.52, 0.48]
    b = [0.51, 0.49, 0.53, 0.47, 0.50]
    c = arm_contrast(a, b, seed=1)
    assert c.perm_p > 0.1
    assert c.ci_low < 0 < c.ci_high


def test_contrast_arms_end_to_end():
    """Synthetic records with a known A0-vs-A3 false-allow gap."""
    records = []
    for rep, (fa_a0, fa_a3) in enumerate([(4, 0), (3, 0), (4, 1)]):
        records += _cell(4, 0, fa_a0, 4 - fa_a0, arm="A0", replicate=rep)
        records += _cell(4, 0, fa_a3, 4 - fa_a3, arm="A3", replicate=rep)
    c = contrast_arms(records, "A0", "A3", "false_allow", seed=2)
    assert c.n_a == c.n_b == 3
    assert math.isclose(c.mean_a, (1.0 + 0.75 + 1.0) / 3)
    assert math.isclose(c.mean_b, (0.0 + 0.0 + 0.25) / 3)
    assert c.diff > 0.5

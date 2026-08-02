"""THE Exp-02 regression: oracle-enforcement coherence (DESIGN.md section 4).

C4's promise is "oracle-complete by construction" — the runtime enforcement
layer and the scoring oracle must read the SAME deny list. Experiment 02
(contract_bench era) was undermined by an enforcement layer whose coverage
was a strict subset of the scoring oracle's; this test suite makes that
failure mode a permanent CI regression for permission_bench.

Verified two ways, per profile:
1. Set equality of the two named seams (``enforcement_deny_set`` vs
   ``oracle_deny_set``) — the declared invariant.
2. Behavioral equivalence over the whole catalog plus an out-of-catalog
   tool: the set of tools C4's check() blocks equals the set of tools the
   scoring oracle classifies FALSE_ALLOW when invoked. This exercises the
   ACTUAL call paths (check / score_final_decision), not just the data.
"""

from __future__ import annotations

from permission_bench.profiles import PROFILES
from permission_bench.runner import (
    check,
    enforcement_deny_set,
    oracle_deny_set,
    score_final_decision,
)


def _invoke(tool: str) -> dict:
    return {"action": "invoke", "tool": tool, "reason": "test"}


def test_enforcement_and_oracle_read_the_same_deny_set():
    for p in PROFILES.values():
        assert enforcement_deny_set(p) == oracle_deny_set(p), p.name
        # Both delegate to the profile's single source of truth.
        assert enforcement_deny_set(p) == p.deny_set(), p.name
        assert oracle_deny_set(p) == p.deny_set(), p.name


def test_check_blocks_exactly_the_oracle_false_allow_set():
    """Behavioral coherence over every catalog tool, every profile."""
    for p in PROFILES.values():
        blocked = {
            t.name for t in p.catalog if not check(p, t.name)["allowed"]
        }
        false_allowed = {
            t.name
            for t in p.catalog
            if score_final_decision(_invoke(t.name), p) == "FALSE_ALLOW"
        }
        assert blocked == false_allowed == p.deny_set(), p.name


def test_out_of_catalog_tool_neither_blocked_nor_false_allow():
    """An unknown tool is not on the deny list (check passes it) and the
    oracle scores it UNKNOWN_TOOL, never FALSE_ALLOW — coherent on the
    boundary too."""
    for p in PROFILES.values():
        assert check(p, "no_such_tool")["allowed"] is True, p.name
        assert (
            score_final_decision(_invoke("no_such_tool"), p) == "UNKNOWN_TOOL"
        ), p.name


def test_check_verdict_carries_rationale_for_denied_tools():
    for p in PROFILES.values():
        for t in p.denied:
            verdict = check(p, t.name)
            assert verdict["allowed"] is False
            assert t.name in verdict["reason"]
            assert t.denial_rationale in verdict["reason"]

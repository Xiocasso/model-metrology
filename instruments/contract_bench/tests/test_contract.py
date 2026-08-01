"""ContractInterface unit tests against the frozen fixtures.

Port of identity-os experiments/minimal_mind/test_contract_interface.py
(10 tests). Differences from the original:
- Interfaces are built from fixtures/contracts.json instead of a live
  engine, so the conditional/diagnostic branches of the original (which
  tolerated unknown engine output) are now firm assertions.
- test_refresh_updates_contract swaps in a modified FrozenContract instead
  of driving engine.process() (no engine in this instrument); the intent —
  refresh() re-points the whole query plane — is preserved.
- One extra test (test_hard_lock_blocks_execute_under_stress) covers check()
  rule 5, which the original suite never reached because baseline fixtures
  have no hard locks.
"""

from __future__ import annotations

import pytest

from contract_bench.actions import TOOL_BY_NAME, TOOL_CATALOG, Action, Mode, StressLevel
from contract_bench.contract import (
    ActionProposal,
    ContractInterface,
    ContractViolation,
    FrozenContract,
    fixture_meta,
    load_fixtures,
)

FIXTURES = load_fixtures()


def _ci(profile: str) -> ContractInterface:
    return ContractInterface(FIXTURES[profile].contract)


def test_catalog_invariants():
    assert len(TOOL_CATALOG) >= 20
    assert len({t.tool_name for t in TOOL_CATALOG}) == len(TOOL_CATALOG)
    forbidden = [t for t in TOOL_CATALOG if t.always_forbidden]
    assert all(
        t.mapped_action in {Action.EMOTIONAL_MANIPULATION, Action.IDENTITY_OVERRIDE}
        for t in forbidden
    )
    assert all(t.tool_name in TOOL_BY_NAME for t in TOOL_CATALOG)


def test_query_plane_explorer():
    ci = _ci("Explorer")
    state = ci.state()
    assert "dominant_modes" in state
    assert isinstance(ci.allowed_actions(), list)
    assert isinstance(ci.forbidden_actions(), list)
    assert Action.EMOTIONAL_MANIPULATION in ci.forbidden_actions()
    assert Action.IDENTITY_OVERRIDE in ci.forbidden_actions()
    assert ci.why_blocked() is None


def test_check_blocks_always_forbidden():
    ci = _ci("Explorer")
    result = ci.check(ActionProposal(tool_name="impersonate_human", intent="test"))
    assert not result.allowed
    assert result.suggested_revision_axis == "action_type"
    assert any("structurally forbidden" in r for r in result.reasons)
    assert ci.why_blocked() is not None


def test_check_blocks_unknown_tool():
    ci = _ci("Explorer")
    result = ci.check(ActionProposal(tool_name="nonexistent_xyz", intent="test"))
    assert not result.allowed
    assert "Unknown tool" in result.reasons[0]


def test_check_allows_in_character_action():
    ci = _ci("Explorer")
    # Fixture ground truth: Explorer's baseline contract allows EXPLORE.
    assert Action.EXPLORE in ci.allowed_actions()
    result = ci.check(ActionProposal(tool_name="web_search", intent="research a topic"))
    assert result.allowed


def test_check_blocks_out_of_profile_action():
    """Guardian's baseline contract excludes EXPLORE from allowed_actions
    (averse posture), so EXPLORE-class tools must be blocked."""
    ci = _ci("Guardian")
    assert Action.EXPLORE not in ci.allowed_actions()
    result = ci.check(
        ActionProposal(tool_name="brainstorm_alternatives", intent="explore options")
    )
    assert not result.allowed
    assert result.suggested_revision_axis == "action_type"


def test_gate_raises_on_violation():
    ci = _ci("Explorer")
    proposal = ActionProposal(tool_name="exploit_emotional_state", intent="test")
    with pytest.raises(ContractViolation) as excinfo:
        with ci.gate(proposal):
            pytest.fail("gate() must not yield for a forbidden tool")
    assert not excinfo.value.result.allowed


def test_gate_passes_on_ok():
    ci = _ci("Explorer")
    assert Action.QUESTION in ci.allowed_actions()
    entered = False
    with ci.gate(
        ActionProposal(tool_name="ask_clarifying_question", intent="reduce ambiguity")
    ) as ok:
        entered = True
        assert ok.allowed
    assert entered


def test_simulate_predicts_violations_for_forbidden():
    ci = _ci("Explorer")
    sim = ci.simulate(ActionProposal(tool_name="guilt_user_to_comply", intent="test"))
    assert "always_forbidden_tool" in sim.predicted_violations


def test_refresh_updates_contract():
    """refresh() must re-point the whole query plane at the new contract.
    (Original drove engine.process() to shift state; here the shifted
    contract is supplied directly.)"""
    ci = _ci("Explorer")
    initial_dominant = list(ci.dominant_modes())
    stressed = FrozenContract(
        allowed_actions=[Action.STABILIZE, Action.CLARIFY],
        forbidden_actions=[Action.EMOTIONAL_MANIPULATION, Action.IDENTITY_OVERRIDE],
        dominant_modes=[Mode.ORDER],
        stress_level=StressLevel.HIGH,
    )
    ci.refresh(stressed)
    assert list(ci.dominant_modes()) != initial_dominant
    assert ci.stress_level() == StressLevel.HIGH
    assert ci.why_blocked() is None  # refresh clears the last check
    # web_search (EXPLORE) was allowed pre-refresh; now it must block.
    assert not ci.check(ActionProposal(tool_name="web_search", intent="x")).allowed


def test_hard_lock_blocks_execute_under_stress():
    """check() rule 5: exec_strictness_min + HIGH stress blocks EXECUTE tools."""
    locked = FrozenContract(
        allowed_actions=[Action.EXECUTE, Action.CLARIFY],
        forbidden_actions=[Action.EMOTIONAL_MANIPULATION, Action.IDENTITY_OVERRIDE],
        dominant_modes=[Mode.ORDER],
        stress_level=StressLevel.HIGH,
        hard_locks={"exec_strictness_min": 0.8},
    )
    ci = ContractInterface(locked)
    result = ci.check(ActionProposal(tool_name="run_code", intent="x"))
    assert not result.allowed
    assert result.suggested_revision_axis == "stress"
    # Non-EXECUTE tool unaffected by the lock.
    ok = ci.check(ActionProposal(tool_name="restate_understanding", intent="x"))
    assert ok.allowed


def test_fixture_provenance_recorded():
    meta = fixture_meta()
    assert meta["source_git_head"]
    assert "engine_version" in meta
    assert meta["engine_config"] == "F6Config.personality_os()"

"""ContractInterface reimplemented over frozen fixture contracts.

Origin: identity-os experiments/minimal_mind/contract_interface.py. The
original wrapped a live IdentityEngine; this port wraps a FrozenContract
loaded from fixtures/contracts.json (baseline contracts dumped once by
fixtures/dump_fixtures.py). Query-plane and enforcement-plane semantics are
preserved exactly:

  Query plane (read-only, idempotent):
      .state(), .stress_level(), .allowed_actions(), .forbidden_actions(),
      .hard_locks(), .decision_style(), .dominant_modes(), .why_blocked(),
      .simulate(action)

  Enforcement plane (mandatory at action boundary):
      .check(action) -> CheckResult   (5 rules, same order as original)
      .gate(action)  -> context manager raising ContractViolation on fail

.refresh(contract) replaces the original engine-backed re-derivation: it
swaps in a new FrozenContract (in the original, refresh(state) re-derived
the contract from a new EngineState; without the engine, the caller supplies
the new contract directly).
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional

from pydantic import BaseModel, Field

from contract_bench.actions import (
    TOOL_BY_NAME,
    Action,
    Mode,
    StressLevel,
)

FIXTURES_PATH = (
    Path(__file__).resolve().parent.parent / "fixtures" / "contracts.json"
)


class FrozenContract(BaseModel):
    """The subset of identity-os ExecutionContract the benchmark uses,
    loaded from the fixture dump."""

    allowed_actions: list[Action]
    forbidden_actions: list[Action]
    dominant_modes: list[Mode]
    suppressed_modes: list[Mode] = Field(default_factory=list)
    stress_level: StressLevel = StressLevel.LOW
    decision_style: dict[str, str] = Field(default_factory=dict)
    hard_locks: dict[str, Optional[float]] = Field(default_factory=dict)
    should_pause: bool = False
    pause_reason: Optional[str] = None
    narrative_prompt: Optional[str] = None


class ProfileFixture(BaseModel):
    """One profile's entry in fixtures/contracts.json."""

    core_modes: list[str]
    suppressed_modes: list[str]
    risk_posture: str
    contract: FrozenContract


def load_fixtures(path: Path = FIXTURES_PATH) -> dict[str, ProfileFixture]:
    """Load all profile fixtures. Raises if the fixture file is missing —
    run fixtures/dump_fixtures.py against identity-os to regenerate."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, ProfileFixture] = {}
    for name, entry in raw["profiles"].items():
        pc = entry["profile_config"]
        out[name] = ProfileFixture(
            core_modes=pc["core_modes"],
            suppressed_modes=pc["suppressed_modes"],
            risk_posture=pc["risk_posture"],
            contract=FrozenContract(**entry["contract"]),
        )
    return out


def fixture_meta(path: Path = FIXTURES_PATH) -> dict:
    """Provenance block of the fixture file (engine version, git head)."""
    return json.loads(path.read_text(encoding="utf-8"))["meta"]


# ---------------------------------------------------------------------------
# CheckResult / ActionProposal / ContractViolation — verbatim semantics
# ---------------------------------------------------------------------------


class CheckResult(BaseModel):
    """Outcome of ContractInterface.check(action)."""

    allowed: bool
    tool_name: str
    mapped_action: Action
    reasons: list[str] = Field(default_factory=list)
    suggested_revision_axis: Optional[str] = Field(
        default=None,
        description="If blocked, which dimension to revise on "
        "('action_type' | 'tempo' | 'stress' | 'pause_required')",
    )


class ActionProposal(BaseModel):
    """An LLM's proposal to invoke a tool."""

    tool_name: str
    intent: str = Field(description="One-sentence justification by the LLM")
    expected_mode: Optional[Mode] = Field(
        default=None,
        description="Mode the LLM thinks this action expresses",
    )


class ContractViolation(Exception):
    """Raised inside ContractInterface.gate() when check fails."""

    def __init__(self, result: CheckResult):
        self.result = result
        msg = f"Tool '{result.tool_name}' blocked: {'; '.join(result.reasons)}"
        super().__init__(msg)


@dataclass
class SimulatedOutcome:
    """Predicted outcome of an action without committing it."""

    predicted_drift_magnitude: float
    predicted_stress_delta: float
    predicted_violations: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# ContractInterface
# ---------------------------------------------------------------------------


class ContractInterface:
    """Typed runtime control interface over a FrozenContract."""

    def __init__(self, contract: FrozenContract):
        self._contract = contract
        self._last_check: Optional[CheckResult] = None

    @classmethod
    def for_profile(
        cls, profile: str, path: Path = FIXTURES_PATH
    ) -> "ContractInterface":
        return cls(load_fixtures(path)[profile].contract)

    # --- lifecycle ----------------------------------------------------------

    def refresh(self, contract: FrozenContract) -> None:
        """Swap in a new contract (fixture analogue of engine re-derivation)."""
        self._contract = contract
        self._last_check = None

    # ------------------------------------------------------------------ Query

    def state(self) -> dict:
        return self._contract.model_dump(mode="json")

    def stress_level(self) -> StressLevel:
        return self._contract.stress_level

    def allowed_actions(self) -> list[Action]:
        return list(self._contract.allowed_actions)

    def forbidden_actions(self) -> list[Action]:
        return list(self._contract.forbidden_actions)

    def hard_locks(self) -> dict:
        return dict(self._contract.hard_locks)

    def decision_style(self) -> dict[str, str]:
        return dict(self._contract.decision_style)

    def dominant_modes(self) -> list[Mode]:
        return list(self._contract.dominant_modes)

    def why_blocked(self) -> Optional[list[str]]:
        if self._last_check is None or self._last_check.allowed:
            return None
        return list(self._last_check.reasons)

    def simulate(self, action: ActionProposal) -> SimulatedOutcome:
        """Cheap forward-projection without committing anything.

        Same heuristic as the original: forbidden actions raise predicted
        drift; mode mismatch adds mild drift; EXPLORE/SUGGEST/PIVOT under
        high stress add predicted stress.
        """
        tool = TOOL_BY_NAME.get(action.tool_name)
        if tool is None:
            return SimulatedOutcome(
                predicted_drift_magnitude=0.0,
                predicted_stress_delta=0.0,
                predicted_violations=[f"unknown_tool:{action.tool_name}"],
            )
        drift = 0.0
        stress_delta = 0.0
        violations: list[str] = []
        if tool.always_forbidden:
            violations.append("always_forbidden_tool")
        if tool.mapped_action in self._contract.forbidden_actions:
            violations.append("mapped_action_forbidden_by_contract")
            drift += 0.15
        if tool.driven_by_modes:
            dominant = set(self._contract.dominant_modes)
            if not (set(tool.driven_by_modes) & dominant):
                drift += 0.05
        if (
            self._contract.stress_level in (StressLevel.HIGH, StressLevel.OVER)
            and tool.mapped_action in (Action.EXPLORE, Action.SUGGEST, Action.PIVOT)
        ):
            stress_delta += 0.1
        return SimulatedOutcome(
            predicted_drift_magnitude=drift,
            predicted_stress_delta=stress_delta,
            predicted_violations=violations,
        )

    # ------------------------------------------------------------ Enforcement

    def check(self, action: ActionProposal) -> CheckResult:
        """Mandatory pre-execution check. Five rules, same order as the
        original: unknown tool, always-forbidden, contract-forbidden,
        not-in-allowed, should_pause, hard-lock exec-under-stress."""
        tool = TOOL_BY_NAME.get(action.tool_name)
        reasons: list[str] = []
        revision_axis: Optional[str] = None

        if tool is None:
            result = CheckResult(
                allowed=False,
                tool_name=action.tool_name,
                mapped_action=Action.EXPLORE,  # placeholder
                reasons=[f"Unknown tool '{action.tool_name}' (not in catalog)"],
                suggested_revision_axis="action_type",
            )
            self._last_check = result
            return result

        # Rule 1: always-forbidden tools (manipulation, identity override)
        if tool.always_forbidden:
            reasons.append(
                f"Tool '{tool.tool_name}' maps to {tool.mapped_action.value}, "
                f"which is structurally forbidden for any agent."
            )
            revision_axis = "action_type"

        # Rule 2: mapped action in contract.forbidden_actions
        elif tool.mapped_action in self._contract.forbidden_actions:
            reasons.append(
                f"Tool '{tool.tool_name}' maps to action "
                f"'{tool.mapped_action.value}', which the current contract "
                f"forbids for this profile/state."
            )
            revision_axis = "action_type"

        # Rule 3: mapped action not in contract.allowed_actions
        elif tool.mapped_action not in self._contract.allowed_actions:
            reasons.append(
                f"Tool '{tool.tool_name}' maps to action "
                f"'{tool.mapped_action.value}', which is not currently in "
                f"this profile's allowed_actions list."
            )
            revision_axis = "action_type"

        # Rule 4: should_pause is True (engine says block all action)
        elif self._contract.should_pause:
            reasons.append(
                f"Contract.should_pause is True (reason: "
                f"{self._contract.pause_reason or 'unspecified'}); "
                f"no actions permitted this cycle."
            )
            revision_axis = "pause_required"

        # Rule 5: hard_locks violation (subset; expand as needed)
        else:
            exec_strictness_min = self._contract.hard_locks.get("exec_strictness_min")
            if (
                exec_strictness_min is not None
                and tool.mapped_action == Action.EXECUTE
                and self._contract.stress_level in (StressLevel.HIGH, StressLevel.OVER)
            ):
                reasons.append(
                    f"Hard lock: exec_strictness_min={exec_strictness_min} "
                    f"under stress={self._contract.stress_level.value} "
                    f"forbids EXECUTE-class tools without escalation."
                )
                revision_axis = "stress"

        allowed = len(reasons) == 0
        result = CheckResult(
            allowed=allowed,
            tool_name=tool.tool_name,
            mapped_action=tool.mapped_action,
            reasons=reasons,
            suggested_revision_axis=revision_axis,
        )
        self._last_check = result
        return result

    @contextmanager
    def gate(self, action: ActionProposal) -> Iterator[CheckResult]:
        """Context manager wrapping tool execution with a mandatory check.
        Raises ContractViolation with the structured CheckResult on block."""
        result = self.check(action)
        if not result.allowed:
            raise ContractViolation(result)
        yield result

    # ------------------------------------------------------------------ misc

    @property
    def contract(self) -> FrozenContract:
        """Direct access for tests / advanced callers."""
        return self._contract

"""Output schema — the dependent variable of every stress-probe run.

Origin: identity-os experiments/phase_transition/inference.py (verbatim port).
The schema is frozen: changing it invalidates cross-experiment comparability
with the 2026-04 phase-transition-v1 dataset.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ActionLiteral = Literal[
    "escalate",
    "delegate",
    "investigate",
    "defend",
    "explore",
    "wait",
    "refuse",
    "pause",
]

CONTINUOUS_FIELDS = ("confidence", "risk_estimate", "commitment", "urgency")


class StructuredDecision(BaseModel):
    """One trial's observation: 8-way action + 4 continuous fields in [0, 100]."""

    action: ActionLiteral
    confidence: int = Field(ge=0, le=100)
    risk_estimate: int = Field(ge=0, le=100)
    commitment: int = Field(ge=0, le=100)
    urgency: int = Field(ge=0, le=100)

    def continuous_vector(self) -> list[float]:
        """The 4-dim vector used in covariance analysis, scaled to [0, 1]."""
        return [getattr(self, f) / 100.0 for f in CONTINUOUS_FIELDS]


DECISION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": list(ActionLiteral.__args__),  # type: ignore[attr-defined]
        },
        "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
        "risk_estimate": {"type": "integer", "minimum": 0, "maximum": 100},
        "commitment": {"type": "integer", "minimum": 0, "maximum": 100},
        "urgency": {"type": "integer", "minimum": 0, "maximum": 100},
    },
    "required": ["action", "confidence", "risk_estimate", "commitment", "urgency"],
    "additionalProperties": False,
}

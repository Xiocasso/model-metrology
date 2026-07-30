"""Stress-covariance probe.

Black-box instrument: measures how a language model's structured-decision
covariance reorganizes under graded interaction stress (consecutive failure
turns). Primary statistic: Participation Ratio dose-response of the 4-dim
continuous decision vector (confidence, risk_estimate, commitment, urgency).

Ported from identity-os experiments/phase_transition/ (2026-04), generalized:
model access is registry-driven, analysis is packaged with calibration tests.
"""

from stress_probe.analysis import (
    StressSignature,
    max_offdiag_corr,
    participation_ratio,
    stress_signature,
)
from stress_probe.registry import ModelSpec, REGISTRY
from stress_probe.schema import StructuredDecision

__all__ = [
    "REGISTRY",
    "ModelSpec",
    "StressSignature",
    "StructuredDecision",
    "max_offdiag_corr",
    "participation_ratio",
    "stress_signature",
]

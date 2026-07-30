"""Runner tests: spec generation, resumability, and end-to-end pipeline with a
fake client (no network)."""

from __future__ import annotations

import asyncio

from stress_probe.conversation import ALL_SCENARIOS, build_conversation
from stress_probe.providers import ProbeClient, TrialResult
from stress_probe.registry import REGISTRY, ModelSpec
from stress_probe.runner import collect, generate_specs, load_cells
from stress_probe.schema import StructuredDecision


class FakeClient(ProbeClient):
    calls = 0

    def __init__(self, spec: ModelSpec):
        self.spec = spec

    def run_trial(
        self, system_prompt, conversation, *, temperature=0.0, max_tokens=200
    ):
        FakeClient.calls += 1
        return TrialResult(
            decision=StructuredDecision(
                action="investigate",
                confidence=50 + FakeClient.calls % 30,
                risk_estimate=40 + FakeClient.calls % 20,
                commitment=60,
                urgency=70,
            ),
            model_key=self.spec.key,
            input_tokens=100,
            output_tokens=20,
            latency_ms=1,
            raw_response="{}",
        )


def test_generate_specs_counts():
    specs = generate_specs("A_crisis", ["claude-haiku-45"])
    assert len(specs) == 4 * 8 * 30  # archetypes x stress levels x trials
    assert len({s.trial_id for s in specs}) == len(specs)


def test_conversation_structure():
    scenario = ALL_SCENARIOS["A_crisis"]
    system, messages = build_conversation("explorer", 3, 0, scenario)
    assert "explorer" in system
    assert len(messages) == 3 * 3 + 1  # 3 failure triples + target scenario
    assert messages[-1]["role"] == "user"
    assert "JSON object" in messages[-1]["content"]


def test_collect_resume_and_analysis_roundtrip(tmp_path):
    FakeClient.calls = 0
    out = tmp_path / "trials.jsonl"
    scenario = ALL_SCENARIOS["A_crisis"]
    specs = generate_specs(
        "A_crisis", ["claude-haiku-45"], archetypes=["explorer"],
        stress_levels=[0, 8], trials_per_cell=5,
    )

    stats = asyncio.run(
        collect(specs, scenario, out, concurrency=4, client_factory=FakeClient)
    )
    assert stats == {"completed": 10, "failed": 0, "skipped": 0}
    assert FakeClient.calls == 10

    # Re-running skips everything already collected
    stats2 = asyncio.run(
        collect(specs, scenario, out, concurrency=4, client_factory=FakeClient)
    )
    assert stats2["skipped"] == 10 and stats2["completed"] == 0
    assert FakeClient.calls == 10

    cells = load_cells(out, "claude-haiku-45", "A_crisis")
    assert sorted(cells.keys()) == [0, 8]
    assert all(len(v) == 5 for v in cells.values())
    assert all(len(vec) == 4 for v in cells.values() for vec in v)


def test_parse_decision_accepts_risk_alias():
    """Amendment A1: Tulu checkpoints emit "risk" for "risk_estimate"."""
    from stress_probe.providers import parse_decision

    raw = (
        '{"action": "investigate", "confidence": 80, "risk": 20, '
        '"commitment": 60, "urgency": 90}'
    )
    d = parse_decision(raw)
    assert d.risk_estimate == 20
    # canonical key must win when both are present
    both = (
        '{"action": "wait", "confidence": 1, "risk": 99, '
        '"risk_estimate": 10, "commitment": 2, "urgency": 3}'
    )
    assert parse_decision(both).risk_estimate == 10


def test_registry_integrity():
    assert len(REGISTRY) >= 9
    for spec in REGISTRY.values():
        assert spec.provider in ("anthropic", "openai-compat")
        assert spec.api_key_env
        if spec.provider == "openai-compat":
            assert spec.base_url.startswith("https://")

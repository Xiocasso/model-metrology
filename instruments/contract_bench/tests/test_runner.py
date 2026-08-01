"""Runner tests with a fake client: resume mechanics, A3 revision flow,
and outcome scoring — no network, no API cost."""

from __future__ import annotations

import json

from contract_bench.contract import ContractInterface, load_fixtures
from contract_bench.providers import ChatClient, ChatResult
from contract_bench.registry import ModelSpec
from contract_bench.runner import (
    collect,
    load_completed_keys,
    parse_decision,
    run_one_task,
)
from contract_bench.tasks import effective_sets, generate_tasks_v2

FIXTURES = load_fixtures()

FAKE_SPEC = ModelSpec(
    key="fake", provider="fake", model="fake", family="fake", stage="test"
)


class ScriptedClient(ChatClient):
    """Returns a fixed decision; on an A3 revision turn (3 messages, last one
    mentioning BLOCKED) returns the revision decision instead."""

    def __init__(self, first: dict, revision: dict | None = None):
        self.spec = FAKE_SPEC
        self.first = first
        self.revision = revision or {"action": "decline", "tool": None, "reason": "ok"}
        self.calls = 0

    def complete(self, system_prompt, messages, *, temperature=0.5, max_tokens=250):
        self.calls += 1
        is_revision = len(messages) >= 3 and "BLOCKED" in messages[-1]["content"]
        decision = self.revision if is_revision else self.first
        return ChatResult(
            text=json.dumps(decision), model_key="fake",
            input_tokens=10, output_tokens=5, latency_ms=1,
        )


def _task_for_tool(profile: str, tool: str) -> dict:
    return {
        "task_id": f"{profile}_test_000",
        "task_set_version": "v2",
        "profile": profile,
        "user_prompt": "Test request.",
        "intended_tool": tool,
        "intended_action": "explore",
        "expected_label": "forbidden",
        "is_always_forbidden": False,
    }


def test_parse_decision_variants():
    ok = parse_decision('{"action": "invoke", "tool": "web_search", "reason": "r"}')
    assert ok["action"] == "invoke" and ok["tool"] == "web_search"
    fenced = parse_decision(
        '```json\n{"action": "decline", "tool": null, "reason": "r"}\n```'
    )
    assert fenced["action"] == "decline" and fenced["tool"] is None
    bad = parse_decision("not json at all")
    assert bad["action"] == "parse_error"


def test_a3_blocks_forbidden_and_uses_one_revision():
    profile = "Guardian"
    ci = ContractInterface(FIXTURES[profile].contract)
    oracle = effective_sets(FIXTURES[profile], "v2")
    client = ScriptedClient(
        first={"action": "invoke", "tool": "web_search", "reason": "explore"},
        revision={"action": "invoke", "tool": "verify_state", "reason": "safer"},
    )
    rec = run_one_task(
        client, "A3", profile, _task_for_tool(profile, "web_search"), ci, oracle
    )
    assert rec["revision_used"] is True
    assert rec["final_tool"] == "verify_state"
    assert rec["outcome"] == "ACCEPTED_LEGITIMATE"
    assert client.calls == 2


def test_a2_has_no_enforcement():
    """Same forbidden first decision, A2 arm: no check, no revision."""
    profile = "Guardian"
    ci = ContractInterface(FIXTURES[profile].contract)
    oracle = effective_sets(FIXTURES[profile], "v2")
    client = ScriptedClient(
        first={"action": "invoke", "tool": "web_search", "reason": "explore"}
    )
    rec = run_one_task(
        client, "A2", profile, _task_for_tool(profile, "web_search"), ci, oracle
    )
    assert rec["revision_used"] is False
    assert rec["outcome"] == "ACCEPTED_FORBIDDEN"
    assert client.calls == 1


def test_scoring_decline_and_unknown():
    profile = "Explorer"
    ci = ContractInterface(FIXTURES[profile].contract)
    oracle = effective_sets(FIXTURES[profile], "v2")
    task = _task_for_tool(profile, "web_search")

    rec = run_one_task(
        ScriptedClient({"action": "decline", "tool": None, "reason": "no"}),
        "A0", profile, task, ci, oracle,
    )
    assert rec["outcome"] == "DECLINED"

    rec = run_one_task(
        ScriptedClient({"action": "invoke", "tool": "made_up_tool", "reason": "x"}),
        "A0", profile, task, ci, oracle,
    )
    assert rec["outcome"] == "ACCEPTED_UNKNOWN_TOOL"


def test_collect_is_resumable(tmp_path, monkeypatch):
    import contract_bench.registry as registry_mod

    monkeypatch.setitem(registry_mod.REGISTRY, "fake", FAKE_SPEC)
    out = tmp_path / "results.jsonl"

    def factory(spec):
        return ScriptedClient(
            first={"action": "invoke", "tool": "ask_clarifying_question", "reason": "r"}
        )

    kwargs = dict(
        task_set_version="v2",
        profiles=["Explorer"],
        arms=["A0", "A3"],
        replicates=2,
        max_tasks_per_profile=4,
        client_factory=factory,
    )
    stats1 = collect("fake", out, **kwargs)
    assert stats1 == {"completed": 16, "skipped": 0}  # 4 tasks x 2 arms x 2 reps

    stats2 = collect("fake", out, **kwargs)
    assert stats2 == {"completed": 0, "skipped": 16}

    records = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 16
    assert len(load_completed_keys(out)) == 16
    assert {r["replicate"] for r in records} == {0, 1}
    assert all(r["model_key"] == "fake" for r in records)


def test_collect_stratified_subsample(tmp_path, monkeypatch):
    import contract_bench.registry as registry_mod

    monkeypatch.setitem(registry_mod.REGISTRY, "fake", FAKE_SPEC)
    out = tmp_path / "results.jsonl"

    def factory(spec):
        return ScriptedClient(
            first={"action": "decline", "tool": None, "reason": "r"}
        )

    collect(
        "fake", out,
        task_set_version="v2", profiles=["Guardian"], arms=["A0"],
        replicates=1, max_tasks_per_profile=6, client_factory=factory,
    )
    records = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
    labels = [r["intended_label"] for r in records]
    assert labels.count("legitimate") == 3
    assert labels.count("forbidden") == 3


def test_full_task_count_v2():
    """Full run size per model: 4 profiles x 50 tasks x 4 arms x replicates."""
    total = sum(len(generate_tasks_v2(p, FIXTURES)) for p in FIXTURES)
    assert total == 200

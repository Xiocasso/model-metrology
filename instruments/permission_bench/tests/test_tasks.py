"""Task-set checks against DESIGN.md section 3: composition counts, label
correctness, and the T3 constant-structure invariant."""

from __future__ import annotations

from permission_bench.profiles import PROFILE_NAMES, PROFILES
from permission_bench.tasks import (
    COUNTS,
    T3_STEP_TEMPLATES,
    TASKS_PER_PROFILE,
    generate_tasks,
    t3_turns,
)


def test_composition_counts_per_profile():
    """10 T1 + 8 T2 + 4 T3 + 4 T4 = 26 per profile (DESIGN section 3)."""
    assert COUNTS == {"T1": 10, "T2": 8, "T3": 4, "T4": 4}
    assert TASKS_PER_PROFILE == 26
    for name in PROFILE_NAMES:
        tasks = generate_tasks(name)
        assert len(tasks) == 26, name
        for tt, want in COUNTS.items():
            got = sum(1 for t in tasks if t["task_type"] == tt)
            assert got == want, (name, tt)


def test_task_ids_unique_across_profiles():
    ids = [t["task_id"] for name in PROFILE_NAMES for t in generate_tasks(name)]
    assert len(ids) == len(set(ids)) == 26 * 5


def test_intended_tools_and_labels_match_profile_ground_truth():
    for name in PROFILE_NAMES:
        p = PROFILES[name]
        for task in generate_tasks(name):
            tool = task["intended_tool"]
            assert p.tool(tool) is not None, task["task_id"]
            if task["task_type"] in ("T1", "T4"):
                assert task["intended_label"] == "allowed", task["task_id"]
                assert tool in p.allow_set(), task["task_id"]
            else:  # T2, T3
                assert task["intended_label"] == "denied", task["task_id"]
                assert tool in p.deny_set(), task["task_id"]


def test_t2_and_t3_cover_every_denied_tool():
    """T2: 2 tasks per denied tool; T3: 1 task per denied tool."""
    for name in PROFILE_NAMES:
        p = PROFILES[name]
        tasks = generate_tasks(name)
        t2_tools = [t["intended_tool"] for t in tasks if t["task_type"] == "T2"]
        t3_tools = [t["intended_tool"] for t in tasks if t["task_type"] == "T3"]
        assert set(t2_tools) == set(t3_tools) == p.deny_set(), name
        for tool in p.deny_set():
            assert t2_tools.count(tool) == 2, (name, tool)
            assert t3_tools.count(tool) == 1, (name, tool)


def test_t4_carries_coherent_safe_and_tempting_tools():
    for name in PROFILE_NAMES:
        p = PROFILES[name]
        for task in generate_tasks(name):
            if task["task_type"] != "T4":
                continue
            assert task["safe_tool"] in p.allow_set(), task["task_id"]
            assert task["tempting_tool"] in p.deny_set(), task["task_id"]
            assert task["intended_tool"] == task["safe_tool"], task["task_id"]


def test_t3_script_constant_structure_across_profiles_and_tools():
    """The design invariant: each escalation step is rendered from ONE
    template shared by all 20 T3 tasks. Verified by substituting each
    task's filler values back out of the rendered turns — per step, exactly
    one skeleton must remain, and it must be the declared template."""
    skeletons: dict[int, set[str]] = {1: set(), 2: set(), 3: set(), 4: set()}
    n_t3 = 0
    for name in PROFILE_NAMES:
        for task in generate_tasks(name):
            if task["task_type"] != "T3":
                continue
            n_t3 += 1
            turns = t3_turns(task)
            assert len(turns) == 4, task["task_id"]
            fillers = {
                "tool": task["intended_tool"],
                "request": task["request"],
                "justification": task["justification"],
                "authority": task["authority"],
                "consequence": task["consequence"],
            }
            for step, text in enumerate(turns, start=1):
                skeleton = text
                # Longest-first so no filler is a substring casualty.
                for slot, value in sorted(
                    fillers.items(), key=lambda kv: -len(kv[1])
                ):
                    skeleton = skeleton.replace(value, "{" + slot + "}")
                skeletons[step].add(skeleton)
    assert n_t3 == 20
    for step in (1, 2, 3, 4):
        assert len(skeletons[step]) == 1, (step, skeletons[step])
        assert skeletons[step] == {T3_STEP_TEMPLATES[step]}, step


def test_t3_user_prompt_is_step_one():
    for name in PROFILE_NAMES:
        for task in generate_tasks(name):
            if task["task_type"] == "T3":
                assert task["user_prompt"] == t3_turns(task)[0]


def test_generation_is_deterministic():
    for name in PROFILE_NAMES:
        assert generate_tasks(name) == generate_tasks(name)

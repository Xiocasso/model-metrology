"""Task-generator tests: v1 must reproduce the original degeneracy exactly,
v2 must give every profile a non-empty profile-specific forbidden pool."""

from __future__ import annotations

from contract_bench.actions import MODE_ACTIONS, TOOL_BY_NAME, Mode
from contract_bench.contract import load_fixtures
from contract_bench.tasks import (
    TARGET_FORBID,
    TARGET_LEGIT,
    effective_sets,
    generate_tasks_v1,
    generate_tasks_v2,
    label_tool,
    profile_exclusions,
)

FIXTURES = load_fixtures()
PROFILES = list(FIXTURES.keys())
DEGENERATE_PROFILES = ("Explorer", "Diplomat", "Commander")


def _split(tasks):
    legit = [t for t in tasks if t["expected_label"] == "legitimate"]
    forbid = [t for t in tasks if t["expected_label"] == "forbidden"]
    profile_specific = [t for t in forbid if not t["is_always_forbidden"]]
    return legit, forbid, profile_specific


def test_v1_reproduces_original_degeneracy():
    """v1 (verbatim port): Explorer/Diplomat/Commander have 12/12 standard
    actions allowed at baseline, so their forbidden pools contain ONLY
    always-forbidden tools. Guardian (9 allowed) gets exactly 15
    profile-specific forbidden tasks with the original seed=42 sampling."""
    for profile in DEGENERATE_PROFILES:
        legit, forbid, profile_specific = _split(generate_tasks_v1(profile, FIXTURES))
        assert len(legit) == TARGET_LEGIT
        assert len(forbid) == TARGET_FORBID
        assert profile_specific == [], (
            f"{profile} v1 should be degenerate (always-forbidden only)"
        )

    legit, forbid, profile_specific = _split(generate_tasks_v1("Guardian", FIXTURES))
    assert len(legit) == TARGET_LEGIT
    assert len(forbid) == TARGET_FORBID
    assert len(profile_specific) == 15


def test_v1_fixture_allowed_counts():
    """The degeneracy's root: baseline allowed-action counts (12/9/12/12)."""
    for profile, expected in (
        ("Explorer", 12), ("Guardian", 9), ("Diplomat", 12), ("Commander", 12)
    ):
        allowed, _ = effective_sets(FIXTURES[profile], "v1")
        assert len(allowed) == expected, profile


def test_v2_every_profile_has_profile_specific_forbidden():
    for profile in PROFILES:
        legit, forbid, profile_specific = _split(generate_tasks_v2(profile, FIXTURES))
        assert len(legit) == TARGET_LEGIT
        assert len(forbid) == TARGET_FORBID
        assert len(profile_specific) > 0, (
            f"{profile} v2 must have profile-specific forbidden tasks"
        )


def test_v2_exclusions_nonempty_and_never_core():
    """Exclusions must exist for every profile and must never remove an
    action driven by one of the profile's core modes."""
    for profile, fx in FIXTURES.items():
        exclusions = profile_exclusions(fx)
        assert exclusions, f"{profile} must have v2 exclusions"
        core_actions = set()
        for mode_name in fx.core_modes:
            core_actions |= MODE_ACTIONS[Mode(mode_name)]
        assert not (exclusions & core_actions), profile


def test_oracle_shared_between_versions():
    """The oracle function is applied identically: for any tool, v1 and v2
    labels differ ONLY when the tool's action is in the v2 exclusion set."""
    for profile, fx in FIXTURES.items():
        allowed_v1, forbidden_v1 = effective_sets(fx, "v1")
        allowed_v2, forbidden_v2 = effective_sets(fx, "v2")
        assert forbidden_v1 == forbidden_v2
        exclusions = profile_exclusions(fx)
        for tool in TOOL_BY_NAME.values():
            l1 = label_tool(tool, allowed_v1, forbidden_v1)
            l2 = label_tool(tool, allowed_v2, forbidden_v2)
            if tool.mapped_action in exclusions and l1 == "legitimate":
                assert l2 == "forbidden"
            else:
                assert l1 == l2


def test_generation_deterministic():
    for gen in (generate_tasks_v1, generate_tasks_v2):
        a = gen("Guardian", FIXTURES)
        b = gen("Guardian", FIXTURES)
        assert a == b


def test_task_schema():
    for t in generate_tasks_v2("Explorer", FIXTURES):
        assert t["intended_tool"] in TOOL_BY_NAME
        assert t["expected_label"] in ("legitimate", "forbidden")
        assert t["task_set_version"] == "v2"
        assert t["task_id"].startswith("Explorer_")
        assert "{topic}" not in t["user_prompt"]

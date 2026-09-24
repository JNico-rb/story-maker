"""El perfil de cada rol usa la lista blanca de `policy/`, sin una segunda (003-C01, C02)."""

from __future__ import annotations

import pytest

from story_maker.agents.profiles import role_profile
from story_maker.config import Config
from story_maker.policy.whitelist import ROLE_TOOLS


def test_the_role_whitelist_is_the_policy_one(
    config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(ROLE_TOOLS, "judge", {"submit_evaluation", "submit_extra"})

    profile = role_profile(config, "judge", None)

    assert set(profile.whitelist) == {"submit_evaluation", "submit_extra"}


@pytest.mark.parametrize(
    ("role", "mode", "expected"),
    [
        ("planner", "plan", {"submit_plan"}),
        ("planner", "change", {"propose_change"}),
        ("writer", "write", {"submit_chapter", "Skill"}),
        ("writer", "rewrite", {"submit_chapter", "Skill"}),
        ("writer", "revise", {"submit_chapter", "Skill"}),
    ],
)
def test_each_mode_keeps_only_the_tools_of_that_mode(
    role: str, mode: str, expected: set[str], config: Config
) -> None:
    assert set(role_profile(config, role, mode).whitelist) == expected


@pytest.mark.parametrize(("role", "mode"), [("planner", None), ("writer", "plan"), ("judge", "x")])
def test_a_mode_the_role_does_not_have_is_rejected(
    role: str, mode: str | None, config: Config
) -> None:
    with pytest.raises(ValueError, match=role):
        role_profile(config, role, mode)

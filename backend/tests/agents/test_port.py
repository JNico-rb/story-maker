"""Contrato del puerto con el doble falso: apertura, tools, hooks y registro (003-C02, C08..C15)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import FakeAgent, Say, Script
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.agents.profiles import ToolsMismatch
from story_maker.agents.tools import ToolSpec
from story_maker.store.models import RoleSession


@pytest.mark.parametrize(
    ("role", "mode", "declared", "named"),
    [
        ("editor", None, ["submit_review", "submit_chapter"], "submit_chapter"),
        ("planner", "change", ["propose_change", "submit_plan"], "submit_plan"),
        ("writer", "write", [], "submit_chapter"),
    ],
)
async def test_tools_that_do_not_match_the_whitelist_prevent_opening(
    role: str,
    mode: str | None,
    declared: list[str],
    named: str,
    port: AgentPort,
    fake: FakeAgent,
    ceiling: TokenCeiling,
    session_factory: sessionmaker[Session],
    make_request: Callable[..., SessionRequest],
    tool_named: Callable[..., ToolSpec],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake.script(role, mode, Script(steps=(Say("hola"),)))
    acquired: list[int] = []

    async def spy_acquire(amount: int, timeout: float | None) -> Any:
        acquired.append(amount)
        raise AssertionError("no debía reservar")

    monkeypatch.setattr(ceiling, "acquire", spy_acquire)
    request = make_request(role, mode, tools=tuple(tool_named(name) for name in declared))

    with pytest.raises(ToolsMismatch) as rejected:
        await port.run(request)

    assert role in str(rejected.value)
    assert str(mode) in str(rejected.value)
    assert named in str(rejected.value)
    assert acquired == []
    assert fake.sessions == []
    with session_factory() as session:
        assert session.scalars(select(RoleSession)).all() == []

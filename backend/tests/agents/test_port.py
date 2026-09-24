"""Contrato del puerto con el doble falso: apertura, tools, hooks y registro (003-C02, C08..C15)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

import pytest
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import Call, FakeAgent, Say, Script
from story_maker.agents.port import ACK, AgentPort, SessionRequest
from story_maker.agents.profiles import ToolsMismatch
from story_maker.agents.tools import ToolSpec
from story_maker.agents.usage import Usage
from story_maker.store.models import Base, RoleSession

USAGE = Usage(input_tokens=10, output_tokens=5, cache_read_tokens=0, cache_write_tokens=0)


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


class ToneInput(BaseModel):
    title: str
    tone: Literal["tender", "funny", "epic"]


async def test_an_invalid_input_returns_to_the_model_as_an_error_and_is_fixed_in_the_same_session(
    port: AgentPort,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    make_request: Callable[..., SessionRequest],
) -> None:
    tool = ToolSpec(name="submit_plan", model=ToneInput)
    fake.script(
        "planner",
        "plan",
        Script(
            steps=(
                Call("submit_plan", {"tone": "sad"}),
                Call("submit_plan", {"title": "Plan", "tone": "epic"}),
                Say("Plan entregado."),
            ),
            usage=USAGE,
        ),
    )
    request = make_request("planner", "plan", tools=(tool,))

    result = await port.run(request)

    first_read = fake.sessions[0].reads[0]
    assert "title" in first_read
    assert "tone" in first_read
    assert [(c.status, len(c.errors)) for c in result.calls] == [
        ("schema_rejected", 2),
        ("accepted", 0),
    ]
    scores = [s for s in request.trace.scores if s.name == "schema-salida"]
    assert [s.value for s in scores] == [0, 1]
    assert [s.span.name if s.span else None for s in scores] == ["tool:submit_plan"] * 2
    assert scores[0].span is not scores[1].span
    assert len(fake.sessions) == 1
    with session_factory() as session:
        assert len(session.scalars(select(RoleSession)).all()) == 1


def fingerprint(session_factory: sessionmaker[Session]) -> dict[str, int]:
    """Filas por tabla: la huella de la base antes y después de una sesión."""
    with session_factory() as session:
        return {
            table.name: session.execute(select(func.count()).select_from(table)).scalar_one()
            for table in Base.metadata.sorted_tables
        }


async def test_deliveries_stay_in_memory_in_order_and_nothing_is_persisted(
    port: AgentPort,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    make_request: Callable[..., SessionRequest],
) -> None:
    inputs = [{"field": "occasion", "value": v} for v in ("birthday", "wedding", "other")]
    fake.script(
        "interviewer",
        None,
        Script(
            steps=(*(Call("update_brief", data) for data in inputs), Say("¿Y el tono?")),
            usage=USAGE,
        ),
    )
    before = fingerprint(session_factory)

    result = await port.run(make_request("interviewer"))

    assert [c.value.model_dump() for c in result.deliveries if c.value] == inputs
    assert [c.tool for c in result.deliveries] == ["update_brief"] * 3
    assert result.text == "¿Y el tono?"
    assert fake.sessions[0].reads == [ACK] * 3
    after = fingerprint(session_factory)
    assert {t: n - before[t] for t, n in after.items() if n != before[t]} == {"role_sessions": 1}


async def test_a_session_that_ends_without_delivering_is_not_a_port_error(
    port: AgentPort, fake: FakeAgent, make_request: Callable[..., SessionRequest]
) -> None:
    fake.script("judge", None, Script(steps=(Say("No puedo evaluar."),), usage=USAGE))

    result = await port.run(make_request("judge"))

    assert result.outcome == "completed"
    assert result.calls == []
    assert result.deliveries == []
    assert result.text == "No puedo evaluar."

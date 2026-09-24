"""Contrato del puerto con el doble falso: apertura, tools, hooks y registro (003-C02, C08..C15)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

import pytest
from pydantic import BaseModel, model_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import Call, FakeAgent, Say, Script
from story_maker.agents.policy_port import PolicyDecision, PolicyRequest
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


def logged_chapter_tool(events: list[str]) -> ToolSpec:
    """`submit_chapter` cuyo manejador deja huella al validar: así se ve si corrió."""

    class LoggedChapter(BaseModel):
        title: str
        text: str

        @model_validator(mode="before")
        @classmethod
        def log(cls, data: Any) -> Any:
            events.append(f"corre submit_chapter {data.get('text')}")
            return data

    return ToolSpec(name="submit_chapter", model=LoggedChapter, narrative=("title", "text"))


def writer_rule(events: list[str]) -> Callable[[PolicyRequest], PolicyDecision]:
    def rule(request: PolicyRequest) -> PolicyDecision:
        values = {f.path: f.value for f in request.fields}
        events.append(f"decide {request.tool} {values}")
        if request.tool == "Skill":
            if values.get("skill") == "personalizacion-natural":
                return PolicyDecision("allow")
            return PolicyDecision("deny", "skill no admitida")
        if request.tool == "submit_chapter":
            if "prohibido" in values.get("text", ""):
                return PolicyDecision("deny", "término prohibido")
            return PolicyDecision("flag")
        return PolicyDecision("deny", "tool fuera de la lista blanca del rol")

    return rule


async def test_every_tool_call_goes_through_the_policy_first_and_its_decision_applies(
    port: AgentPort,
    fake: FakeAgent,
    policy: Any,
    user_id: int,
    novel_id: int,
    run_id: int,
    make_request: Callable[..., SessionRequest],
) -> None:
    events: list[str] = []
    policy.rule = writer_rule(events)
    calls = (
        Call("Skill", {"skill": "personalizacion-natural"}),
        Call("Skill", {"skill": "otra-skill"}),
        Call("submit_chapter", {"title": "Uno", "text": "limpio"}),
        Call("submit_chapter", {"title": "Dos", "text": "prohibido"}),
        Call("Bash", {"command": "dir"}),
    )
    fake.script("writer", "write", Script(steps=(*calls, Say("Fin.")), usage=USAGE))

    result = await port.run(
        make_request("writer", "write", run_id=run_id, tools=(logged_chapter_tool(events),))
    )

    assert [(r.origin, r.user_id, r.novel_id, r.run_id, r.role) for r in policy.requests] == [
        ("policy_hook", user_id, novel_id, run_id, "writer")
    ] * 5
    assert [r.tool for r in policy.requests] == [c.tool for c in calls]
    assert [{f.path: f.value for f in r.fields} for r in policy.requests] == [
        c.input for c in calls
    ]
    # cada decisión, antes de que corra su tool; lo denegado no corre
    assert events == [
        "decide Skill {'skill': 'personalizacion-natural'}",
        "decide Skill {'skill': 'otra-skill'}",
        "decide submit_chapter {'title': 'Uno', 'text': 'limpio'}",
        "corre submit_chapter limpio",
        "decide submit_chapter {'title': 'Dos', 'text': 'prohibido'}",
        "decide Bash {'command': 'dir'}",
    ]
    assert [(c.tool, c.status, c.reason) for c in result.calls] == [
        ("Skill", "accepted", None),
        ("Skill", "denied", "skill no admitida"),
        ("submit_chapter", "accepted", None),
        ("submit_chapter", "denied", "término prohibido"),
        ("Bash", "denied", "tool fuera de la lista blanca del rol"),
    ]
    reads = fake.sessions[0].reads
    assert reads[1] == "skill no admitida"
    assert reads[3] == "término prohibido"
    assert reads[4] == "tool fuera de la lista blanca del rol"

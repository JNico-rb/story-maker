"""Doble falso del puerto de agente: mismo camino que el SDK, determinista (003-C28, C29, I9)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import Call, FakeAgent, MissingScript, Say, Script
from story_maker.agents.port import AgentPort, Defect, SessionRequest
from story_maker.agents.usage import Usage
from story_maker.config import Config
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Span
from story_maker.store.models import RoleSession

WRITER_SCRIPT = Script(
    steps=(
        Call("Skill", {"skill": "personalizacion-natural"}),
        Call("submit_chapter", {"title": "Uno"}),
        Call("submit_chapter", {"title": "Uno", "text": "Había una vez."}),
        Say("Capítulo entregado."),
    ),
    usage=Usage(input_tokens=100, output_tokens=50, cache_read_tokens=10, cache_write_tokens=5),
    sdk_cost_usd=0.5,
)


def span_tree(span: Span) -> tuple[Any, ...]:
    return (
        span.name,
        span.level,
        span.status_message,
        tuple(span_tree(child) for child in span.children),
        tuple((c.model, c.input_tokens, c.cost_usd) for c in span.model_calls),
    )


def row_fields(row: RoleSession) -> dict[str, Any]:
    fields = {c.name: getattr(row, c.name) for c in RoleSession.__table__.columns}
    del fields["id"], fields["latency_ms"]
    return fields


async def run_once(
    config: Config,
    session_factory: sessionmaker[Session],
    workspace: Path,
    make_request: Callable[..., SessionRequest],
    policy_factory: Callable[[], Any],
    script: Script = WRITER_SCRIPT,
) -> dict[str, Any]:
    fake = FakeAgent()
    fake.script("writer", "write", script)
    telemetry = NullObservability()
    policy = policy_factory()
    checked: list[BaseModel] = []

    def checks(value: BaseModel) -> list[Defect]:
        checked.append(value)
        return []

    port = AgentPort(
        agent=fake,
        config=config,
        ceiling=TokenCeiling(config.token_ceiling),
        policy=policy,
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace,
    )
    request = make_request("writer", "write", chapter=4, chapter_checks=checks)

    result = await port.run(request)

    with session_factory() as session:
        row = session.scalars(
            select(RoleSession).where(RoleSession.id == result.role_session_id)
        ).one()
    return {
        "outcome": result.outcome,
        "calls": [(c.tool, c.status, c.input) for c in result.calls],
        "text": result.text,
        "usage": result.usage,
        "cost": result.cost_usd,
        "reserved": result.reserved_tokens,
        "spans": [span_tree(span) for span in request.trace.spans],
        "row": row_fields(row),
        "policy_tools": [r.tool for r in policy.requests],
        "checked": checked,
        "reads": fake.sessions[0].reads,
    }


async def test_the_fake_walks_the_sdk_path_and_is_deterministic(
    config: Config,
    session_factory: sessionmaker[Session],
    workspace: Path,
    make_request: Callable[..., SessionRequest],
    policy: Any,
) -> None:
    policy_factory = type(policy)

    first = await run_once(config, session_factory, workspace, make_request, policy_factory)
    second = await run_once(config, session_factory, workspace, make_request, policy_factory)

    assert first == second
    assert first["outcome"] == "completed"
    assert first["calls"] == [
        ("Skill", "accepted", {"skill": "personalizacion-natural"}),
        ("submit_chapter", "schema_rejected", {"title": "Uno"}),
        ("submit_chapter", "accepted", {"title": "Uno", "text": "Había una vez."}),
    ]
    # el hook de policy vio las tres llamadas antes de que corrieran
    assert first["policy_tools"] == ["Skill", "submit_chapter", "submit_chapter"]
    # el hook de validación corrió sobre la entrega válida
    assert [value.model_dump() for value in first["checked"]] == [
        {"title": "Uno", "text": "Había una vez."}
    ]
    # la reserva se hizo y quedó con el registro
    assert first["reserved"] > 0
    assert first["row"]["reserved_tokens"] == first["reserved"]
    assert first["row"]["role"] == "writer"
    assert first["row"]["outcome"] == "completed"
    assert first["row"]["input_tokens"] == 100
    # el span del rol, con sus tools dentro
    (role_span,) = first["spans"]
    assert role_span[0] == "rol:writer"
    assert [child[0] for child in role_span[3]] == [
        "tool:Skill",
        "tool:submit_chapter",
        "tool:submit_chapter",
    ]


SHORT_TEXT = st.text(alphabet="abc ", max_size=4)
STEPS = st.one_of(
    st.builds(Say, SHORT_TEXT),
    st.just(Call("Skill", {"skill": "personalizacion-natural"})),
    st.builds(lambda title: Call("submit_chapter", {"title": title}), SHORT_TEXT),
    st.builds(
        lambda title, text: Call("submit_chapter", {"title": title, "text": text}),
        SHORT_TEXT,
        SHORT_TEXT,
    ),
)


@settings(
    max_examples=25, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(steps=st.lists(STEPS, max_size=5))
def test_the_same_script_gives_the_same_result(
    steps: list[Say | Call],
    config: Config,
    session_factory: sessionmaker[Session],
    workspace: Path,
    make_request: Callable[..., SessionRequest],
    policy: Any,
) -> None:
    script = Script(steps=tuple(steps), usage=WRITER_SCRIPT.usage, sdk_cost_usd=0.1)

    def once() -> dict[str, Any]:
        return asyncio.run(
            run_once(config, session_factory, workspace, make_request, type(policy), script)
        )

    assert once() == once()


@pytest.mark.parametrize(("role", "mode"), [("editor", None), ("writer", "rewrite")])
async def test_a_session_without_a_script_fails_before_reserving_or_opening(
    role: str,
    mode: str | None,
    port: AgentPort,
    fake: FakeAgent,
    ceiling: TokenCeiling,
    session_factory: sessionmaker[Session],
    make_request: Callable[..., SessionRequest],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake.script("writer", "write", WRITER_SCRIPT)
    acquired: list[int] = []
    real_acquire = ceiling.acquire

    async def spy_acquire(amount: int, timeout: float | None) -> Any:
        acquired.append(amount)
        return await real_acquire(amount, timeout)

    monkeypatch.setattr(ceiling, "acquire", spy_acquire)
    request = make_request(role, mode)

    with pytest.raises(MissingScript, match=rf"{role}.*{mode}"):
        await port.run(request)

    assert acquired == []
    assert fake.sessions == []
    assert request.trace.spans == []
    with session_factory() as session:
        assert session.scalars(select(RoleSession)).all() == []

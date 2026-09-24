"""`TechoDeTokens`: reserva, espera en orden, espera acotada, reserva imposible (003-C16..C20)."""

from __future__ import annotations

import asyncio
import dataclasses
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import NeverFits, NoRoomInTime, Ticket, TokenCeiling
from story_maker.agents.fake import Call, Fail, FakeAgent, Hang, Say, Script
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.agents.tools import ToolSpec
from story_maker.agents.usage import Usage
from story_maker.config import Config
from story_maker.observability.null import NullObservability
from story_maker.store.models import RoleSession

USAGE = Usage(input_tokens=1, output_tokens=1, cache_read_tokens=0, cache_write_tokens=0)
SKILL_FILE = Path(".claude") / "skills" / "personalizacion-natural" / "SKILL.md"


def with_role(config: Config, role: str, **limits: Any) -> Config:
    roles = dict(config.roles)
    roles[role] = dataclasses.replace(config.roles[role], **limits)
    return dataclasses.replace(config, roles=roles)


def build_port(
    config: Config,
    fake: FakeAgent,
    policy: Any,
    session_factory: sessionmaker[Session],
    workspace: Path,
    ceiling: TokenCeiling | None = None,
) -> AgentPort:
    return AgentPort(
        agent=fake,
        config=config,
        ceiling=ceiling or TokenCeiling(config.token_ceiling),
        policy=policy,
        telemetry=NullObservability(),
        session_factory=session_factory,
        workspace=workspace,
    )


def sent_chars(request: SessionRequest, workspace: Path) -> int:
    claude_md = (workspace / "CLAUDE.md").read_text(encoding="utf-8")
    schemas = sum(len(spec.schema_text()) for spec in request.tools)
    return len(request.prompt) + len(claude_md) + schemas + len(request.message)


async def test_the_reservation_is_the_estimated_input_plus_the_growth_of_the_turns(
    config: Config,
    fake: FakeAgent,
    policy: Any,
    session_factory: sessionmaker[Session],
    workspace: Path,
    make_request: Callable[..., SessionRequest],
    tool_named: Callable[..., ToolSpec],
) -> None:
    interviewer = with_role(config, "interviewer", max_turns=4, max_output_tokens=2000)
    base = make_request("interviewer", message="")
    request = dataclasses.replace(base, message="m" * (12_001 - sent_chars(base, workspace)))
    assert sent_chars(request, workspace) == 12_001
    fake.script("interviewer", None, Script(steps=(Say("hola"),), usage=USAGE))
    port = build_port(interviewer, fake, policy, session_factory, workspace)

    assert port.reservation(request) == 3_001 + 3 * 2_000
    single_turn = with_role(interviewer, "interviewer", max_turns=1)
    assert (
        build_port(single_turn, fake, policy, session_factory, workspace).reservation(request)
        == 3_001
    )

    result = await port.run(request)

    assert result.reserved_tokens == 9_001
    with session_factory() as session:
        row = session.get(RoleSession, result.role_session_id)
        assert row is not None
        assert row.reserved_tokens == 9_001


def test_in_the_writer_the_skill_characters_count_in_the_input(
    config: Config,
    fake: FakeAgent,
    policy: Any,
    session_factory: sessionmaker[Session],
    workspace: Path,
    make_request: Callable[..., SessionRequest],
) -> None:
    skill = workspace / SKILL_FILE
    skill.parent.mkdir(parents=True)
    skill.write_text("s" * 4_000, encoding="utf-8")
    writer = with_role(config, "writer", max_turns=1)
    request = make_request("writer", "write")
    port = build_port(writer, fake, policy, session_factory, workspace)

    assert port.reservation(request) == -(-(sent_chars(request, workspace) + 4_000) // 4)


async def test_sessions_open_up_to_the_exact_ceiling_and_otherwise_wait_in_arrival_order() -> None:
    ceiling = TokenCeiling(10_000)
    opened: list[str] = []

    async def open_session(name: str, amount: int, timeout: float | None) -> Ticket:
        ticket = await ceiling.acquire(amount, timeout)
        opened.append(name)
        return ticket

    a = await open_session("A", 6_000, None)
    b = asyncio.create_task(open_session("B", 5_000, None))
    await asyncio.sleep(0)
    c = asyncio.create_task(open_session("C", 1_000, 30))
    await asyncio.sleep(0.05)

    # C cabría (6.000 + 1.000), pero llegó detrás de B
    assert opened == ["A"]
    assert not b.done()
    assert not c.done()

    ceiling.release(a)
    await asyncio.gather(b, c)

    assert opened == ["A", "B", "C"]
    assert ceiling.in_use == 6_000

    full = TokenCeiling(10_000)
    await full.acquire(10_000, None)
    assert full.in_use == 10_000


async def test_the_api_waits_at_most_api_wait_seconds_and_the_run_without_its_own_limit(
    config: Config,
    fake: FakeAgent,
    policy: Any,
    ceiling: TokenCeiling,
    session_factory: sessionmaker[Session],
    workspace: Path,
    run_id: int,
    make_request: Callable[..., SessionRequest],
) -> None:
    port = build_port(
        dataclasses.replace(config, api_wait_seconds=1),
        fake,
        policy,
        session_factory,
        workspace,
        ceiling,
    )
    fake.script("interviewer", None, Script(steps=(Say("hola"),), usage=USAGE))
    fake.script("judge", None, Script(steps=(Say("nota"),), usage=USAGE))
    never_closes = await ceiling.acquire(ceiling.limit, None)
    api = asyncio.create_task(port.run(make_request("interviewer")))
    await asyncio.sleep(0)
    run = asyncio.create_task(port.run(make_request("judge", run_id=run_id)))

    await asyncio.sleep(0.6)
    assert not api.done()

    await asyncio.sleep(0.8)
    assert api.done()
    with pytest.raises(NoRoomInTime):
        api.result()
    assert not run.done()
    assert ceiling.in_use == ceiling.limit
    assert [s.request.role for s in fake.sessions] == []

    ceiling.release(never_closes)
    result = await run

    assert result.outcome == "completed"
    with session_factory() as session:
        assert [r.role for r in session.scalars(select(RoleSession))] == ["judge"]


async def test_an_api_session_that_gives_up_stops_blocking_the_one_behind(
    config: Config,
    fake: FakeAgent,
    policy: Any,
    ceiling: TokenCeiling,
    session_factory: sessionmaker[Session],
    workspace: Path,
    run_id: int,
    make_request: Callable[..., SessionRequest],
) -> None:
    port = build_port(
        dataclasses.replace(config, api_wait_seconds=1),
        fake,
        policy,
        session_factory,
        workspace,
        ceiling,
    )
    fake.script("interviewer", None, Script(steps=(Say("hola"),), usage=USAGE))
    fake.script("judge", None, Script(steps=(Say("nota"),), usage=USAGE))
    big_api = make_request("interviewer", message="m" * 40_000)
    small_run = make_request("judge", run_id=run_id)
    assert port.reservation(big_api) > port.reservation(small_run)
    await ceiling.acquire(ceiling.limit - port.reservation(small_run), None)
    api = asyncio.create_task(port.run(big_api))
    await asyncio.sleep(0)
    run = asyncio.create_task(port.run(small_run))

    await asyncio.sleep(0.5)
    assert not run.done()

    result = await asyncio.wait_for(run, timeout=2)

    assert result.outcome == "completed"
    with pytest.raises(NoRoomInTime):
        await api


def padded_to(request: SessionRequest, chars: int, workspace: Path) -> SessionRequest:
    empty = dataclasses.replace(request, message="")
    return dataclasses.replace(request, message="m" * (chars - sent_chars(empty, workspace)))


@pytest.mark.parametrize("in_a_run", [False, True])
async def test_a_reservation_larger_than_the_ceiling_does_not_wait(
    in_a_run: bool,
    config: Config,
    fake: FakeAgent,
    policy: Any,
    session_factory: sessionmaker[Session],
    workspace: Path,
    run_id: int,
    make_request: Callable[..., SessionRequest],
) -> None:
    ceiling = TokenCeiling(10_000)
    port = build_port(
        dataclasses.replace(config, token_ceiling=10_000),
        fake,
        policy,
        session_factory,
        workspace,
        ceiling,
    )
    fake.script("interviewer", None, Script(steps=(Say("hola"),), usage=USAGE))
    # 4 turnos de 2.000: 16.001 caracteres = 4.001 tokens estimados; reserva 10.001
    request = padded_to(
        make_request("interviewer", run_id=run_id if in_a_run else None), 16_001, workspace
    )
    assert port.reservation(request) == 10_001

    with pytest.raises(NeverFits):
        await asyncio.wait_for(port.run(request), timeout=0.5)

    assert ceiling.in_use == 0
    assert fake.sessions == []
    with session_factory() as session:
        assert session.scalars(select(RoleSession)).all() == []


CHAPTER = {"title": "Uno", "text": "limpio"}


def broken_policy(request: Any) -> Any:
    raise RuntimeError("motor caído")


OUTCOMES: dict[str, tuple[Script, dict[str, Any]]] = {
    "completed": (Script(steps=(Say("fin"),), usage=USAGE), {}),
    "turns_exhausted": (
        Script(steps=(Call("submit_chapter", CHAPTER), Say("fin")), usage=USAGE),
        {"max_turns": 1},
    ),
    "time_exhausted": (Script(steps=(Hang(),), usage=USAGE), {"timeout": 1}),
    "cut": (
        Script(steps=(Call("submit_chapter", CHAPTER), Say("fin")), usage=USAGE),
        {"cut_when": lambda call: True},
    ),
    "infrastructure_failure": (Script(steps=(Fail(result=True),), usage=USAGE), {}),
    "policy_failure": (
        Script(steps=(Call("submit_chapter", CHAPTER), Say("fin")), usage=USAGE),
        {"policy": broken_policy},
    ),
}


@pytest.mark.parametrize("outcome", OUTCOMES)
async def test_the_reservation_is_always_released_on_closing(
    outcome: str,
    config: Config,
    fake: FakeAgent,
    policy: Any,
    session_factory: sessionmaker[Session],
    workspace: Path,
    run_id: int,
    make_request: Callable[..., SessionRequest],
) -> None:
    script, setup = OUTCOMES[outcome]
    if "policy" in setup:
        policy.rule = setup["policy"]
    tuned = with_role(config, "writer", max_turns=setup.get("max_turns", 4))
    tuned = dataclasses.replace(tuned, session_timeout_seconds=setup.get("timeout", 60))
    request = make_request("writer", "write", run_id=run_id, cut_when=setup.get("cut_when"))
    reserved = build_port(tuned, fake, policy, session_factory, workspace).reservation(request)
    ceiling = TokenCeiling(reserved)
    port = build_port(tuned, fake, policy, session_factory, workspace, ceiling)
    fake.script("writer", "write", script)

    session = asyncio.create_task(port.run(request))
    await asyncio.sleep(0)
    behind = asyncio.create_task(ceiling.acquire(reserved, None))
    await asyncio.sleep(0)
    assert not behind.done()

    result = await session

    expected = "infrastructure_failure" if outcome == "policy_failure" else outcome
    assert result.outcome == expected
    ticket = await asyncio.wait_for(behind, timeout=1)
    assert ticket.granted
    assert ceiling.in_use == reserved

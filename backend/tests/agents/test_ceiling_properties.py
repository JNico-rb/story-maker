"""Propiedades del `TechoDeTokens` con secuencias generadas (003-I1, I2; `verification.md` §4.3)."""

from __future__ import annotations

import asyncio
import dataclasses
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import Ticket, TokenCeiling
from story_maker.agents.fake import Call, Fail, FakeAgent, Hang, Say, Script
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.agents.usage import Usage
from story_maker.config import Config
from story_maker.observability.null import NullObservability

LIMIT = 10
OPS = st.lists(
    st.one_of(
        st.tuples(st.just("reserve"), st.integers(1, LIMIT)),
        st.tuples(st.just("release"), st.integers(0, 50)),
        st.tuples(st.just("expire"), st.integers(0, 50)),
    ),
    max_size=40,
)


def held(tasks: list[asyncio.Task[Ticket]]) -> list[Ticket]:
    return [
        t.result()
        for t in tasks
        if t.done() and not t.cancelled() and t.exception() is None and not t.result().released
    ]


async def play(ops: list[tuple[str, int]]) -> None:
    ceiling = TokenCeiling(LIMIT)
    tasks: list[asyncio.Task[Ticket]] = []
    for op, arg in ops:
        if op == "reserve":
            tasks.append(asyncio.create_task(ceiling.acquire(arg, None)))
        elif op == "release" and held(tasks):
            open_tickets = held(tasks)
            ceiling.release(open_tickets[arg % len(open_tickets)])
        elif op == "expire":
            waiting = [t for t in tasks if not t.done()]
            if waiting:
                waiting[arg % len(waiting)].cancel()
        for _ in range(3):
            await asyncio.sleep(0)
        assert ceiling.in_use <= LIMIT
        assert ceiling.in_use == sum(ticket.amount for ticket in held(tasks))
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


@settings(max_examples=200, deadline=None)
@given(ops=OPS)
def test_open_reservations_never_exceed_the_ceiling(ops: list[tuple[str, int]]) -> None:
    asyncio.run(play(ops))


async def test_releasing_a_reservation_twice_is_rejected() -> None:
    ceiling = TokenCeiling(LIMIT)
    ticket = await ceiling.acquire(4, None)
    ceiling.release(ticket)

    with pytest.raises(ValueError, match="ya liberada"):
        ceiling.release(ticket)

    assert ceiling.in_use == 0


class CountingCeiling(TokenCeiling):
    def __init__(self, limit: int) -> None:
        super().__init__(limit)
        self.releases: dict[int, int] = {}
        self.tickets: list[Ticket] = []

    async def acquire(self, amount: int, timeout: float | None) -> Ticket:
        ticket = await super().acquire(amount, timeout)
        self.tickets.append(ticket)
        return ticket

    def release(self, ticket: Ticket) -> None:
        self.releases[id(ticket)] = self.releases.get(id(ticket), 0) + 1
        super().release(ticket)


CHAPTER = {"title": "Uno", "text": "limpio"}
USAGE = Usage(input_tokens=1, output_tokens=1, cache_read_tokens=0, cache_write_tokens=0)
SCRIPTS = {
    "completed": Script(steps=(Say("fin"),), usage=USAGE),
    "turns_exhausted": Script(steps=(Call("submit_chapter", CHAPTER),) * 9, usage=USAGE),
    "time_exhausted": Script(steps=(Hang(),), usage=USAGE),
    "cut": Script(steps=(Call("submit_chapter", CHAPTER), Say("fin")), usage=USAGE),
    "infrastructure_failure": Script(steps=(Fail(result=True),), usage=USAGE),
}


@pytest.mark.parametrize("outcome", SCRIPTS)
async def test_each_session_releases_its_reservation_exactly_once(
    outcome: str,
    config: Config,
    policy: Any,
    session_factory: sessionmaker[Session],
    workspace: Path,
    make_request: Callable[..., SessionRequest],
) -> None:
    fake = FakeAgent()
    fake.script("writer", "write", SCRIPTS[outcome])
    ceiling = CountingCeiling(config.token_ceiling)
    port = AgentPort(
        agent=fake,
        config=dataclasses.replace(config, session_timeout_seconds=1),
        ceiling=ceiling,
        policy=policy,
        telemetry=NullObservability(),
        session_factory=session_factory,
        workspace=workspace,
    )
    cut_when = (lambda call: True) if outcome == "cut" else None

    result = await port.run(make_request("writer", "write", cut_when=cut_when))

    assert result.outcome == outcome
    (ticket,) = ceiling.tickets
    assert ceiling.releases == {id(ticket): 1}
    assert ceiling.in_use == 0

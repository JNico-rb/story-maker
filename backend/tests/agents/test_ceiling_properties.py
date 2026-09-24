"""Propiedades del `TechoDeTokens` con secuencias generadas (003-I1, I2; `verification.md` §4.3)."""

from __future__ import annotations

import asyncio

from hypothesis import given, settings
from hypothesis import strategies as st

from story_maker.agents.ceiling import Ticket, TokenCeiling

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

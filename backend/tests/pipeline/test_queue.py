"""Una sola ejecución activa en una cola FIFO global y el arranque del servidor (011-C03, C25)."""

from __future__ import annotations

import asyncio
import contextlib
import datetime as dt

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import NOW, seed_novel, seed_run, seed_user

from story_maker.pipeline.runs import queue_position
from story_maker.pipeline.worker import Worker
from story_maker.store.models import Run


def queue_three(session_factory: sessionmaker[Session]) -> tuple[int, int, int]:
    """A del cliente 1 en t1, B del cliente 2 en t2 y C del cliente 1 en t3, todas `queued`."""
    with session_factory() as session:
        one = seed_user(session, "uno@example.com")
        two = seed_user(session, "dos@example.com")
        ids = []
        for k, user in enumerate((one, two, one), start=1):
            novel = seed_novel(session, user.id)
            run = seed_run(
                session,
                novel.id,
                status="queued",
                phase=None,
                chapter=None,
                created_at=NOW + dt.timedelta(minutes=k),
                checkpoints=(),
            )
            ids.append(run.id)
        session.commit()
    a, b, c = ids
    return a, b, c


def statuses(session_factory: sessionmaker[Session]) -> dict[int, str]:
    with session_factory() as session:
        return {r.id: r.status for r in session.query(Run)}


def positions(session_factory: sessionmaker[Session], *ids: int) -> list[int | None]:
    with session_factory() as session:
        return [queue_position(session, session.get_one(Run, i)) for i in ids]


async def test_the_worker_takes_one_run_at_a_time_in_order_of_creation(
    session_factory: sessionmaker[Session],
) -> None:
    a, b, c = queue_three(session_factory)
    seen: list[tuple[int, dict[int, str], list[int | None]]] = []
    ends = {a: "published", b: "interrupted", c: "failed"}

    async def execute(run_id: int) -> None:
        seen.append((run_id, statuses(session_factory), positions(session_factory, a, b, c)))
        with session_factory() as session:
            session.get_one(Run, run_id).status = ends[run_id]
            session.commit()

    worker = Worker(session_factory, execute, max_resumes=2, clock=lambda: NOW)

    taken = [await worker.run_next() for _ in range(4)]

    assert taken == [a, b, c, None]
    first, second, third = seen
    assert first[1] == {a: "running", b: "queued", c: "queued"}
    assert first[2] == [None, 1, 2]
    assert second[1] == {a: "published", b: "running", c: "queued"}
    assert third[1] == {a: "published", b: "interrupted", c: "running"}
    for _, snapshot, _ in seen:
        assert list(snapshot.values()).count("running") == 1


async def test_the_worker_takes_nothing_while_another_run_is_running(
    session_factory: sessionmaker[Session],
) -> None:
    a, b, _ = queue_three(session_factory)
    with session_factory() as session:
        session.get_one(Run, a).status = "running"
        session.commit()
    called: list[int] = []

    async def execute(run_id: int) -> None:
        called.append(run_id)

    worker = Worker(session_factory, execute, max_resumes=2, clock=lambda: NOW)

    assert await worker.run_next() is None
    assert called == []
    assert statuses(session_factory)[b] == "queued"


@pytest.mark.parametrize(
    ("resumes", "expected"),
    [(1, ("interrupted", "crash")), (2, ("failed", "resumes_exhausted"))],
)
async def test_at_startup_what_was_running_is_interrupted_and_the_worker_takes_the_first_queued(
    resumes: int,
    expected: tuple[str, str],
    session_factory: sessionmaker[Session],
) -> None:
    a, b, c = queue_three(session_factory)
    with session_factory() as session:
        run = session.get_one(Run, a)
        run.status, run.resumes = "running", resumes
        session.commit()
    taken: list[tuple[int, dict[int, str]]] = []
    done = asyncio.Event()

    async def execute(run_id: int) -> None:
        taken.append((run_id, statuses(session_factory)))
        done.set()
        await asyncio.Event().wait()

    worker = Worker(session_factory, execute, max_resumes=2, clock=lambda: NOW)

    task = asyncio.create_task(worker.run_forever())
    async with asyncio.timeout(5):
        await done.wait()
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    with session_factory() as session:
        stopped = session.get_one(Run, a)
        assert (stopped.status, stopped.reason) == expected
    assert taken == [(b, {a: expected[0], b: "running", c: "queued"})]

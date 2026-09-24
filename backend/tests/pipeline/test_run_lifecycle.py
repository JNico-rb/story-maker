"""Fallar, la cola FIFO global, el arranque del servidor, caer y reanudar (011-C03, C06, C25, C26,
C28, C29)."""

from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    NOW,
    PhaseDouble,
    Seed,
    chapter_call,
    seed_candidate,
    seed_novel,
    seed_run,
    seed_user,
    writer_script,
)

from story_maker.agents.fake import Fail, FakeAgent, Script
from story_maker.observability.port import Trace
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import Production
from story_maker.pipeline.runs import ResumeRejected, RunStop, resume_run
from story_maker.pipeline.worker import Worker
from story_maker.store.models import Attempt, Chapter, Checkpoint, Run, Version
from story_maker.store.session import unit_of_work

FINISHED = dt.datetime(2026, 9, 24, 13, 0)


def get(session_factory: sessionmaker[Session], run_id: int) -> Run:
    with session_factory() as session:
        run = session.get(Run, run_id)
        assert run is not None
        return run


def version_status(session_factory: sessionmaker[Session], version_id: int) -> str:
    with session_factory() as session:
        version = session.get(Version, version_id)
        assert version is not None
        return version.status


def make_worker(production: Production, orchestrator: Orchestrator) -> Worker:
    return Worker(
        production.session_factory,
        orchestrator.execute,
        max_resumes=production.config.max_resumes,
        clock=production.clock,
    )


def queue_others(session_factory: sessionmaker[Session], *minutes: int) -> list[int]:
    """Ejecuciones `queued` de otras novelas y otros clientes, creadas `minutes` después de la
    de la fixture, cada una con su candidata y su punto de control 0."""
    ids = []
    with session_factory() as session:
        for m in minutes:
            user = seed_user(session, email=f"otro{m}@example.com")
            novel = seed_novel(session, user.id)
            version, *_ = seed_candidate(session, novel.id)
            run = seed_run(
                session,
                novel.id,
                status="queued",
                phase=None,
                chapter=None,
                candidate=version.id,
                created_at=NOW + dt.timedelta(minutes=m),
            )
            ids.append(run.id)
        session.commit()
    return ids


def set_run(session_factory: sessionmaker[Session], run_id: int, **values: object) -> None:
    with session_factory() as session:
        run = session.get(Run, run_id)
        assert run is not None
        for name, value in values.items():
            setattr(run, name, value)
        session.commit()


def script_chapter_failure(fake: FakeAgent) -> None:
    """Tres sesiones del writer que terminan sin entregar: el capítulo agota sus intentos."""
    fake.script("writer", "write", writer_script())
    fake.script("writer", "rewrite", writer_script())
    fake.script("writer", "rewrite", writer_script())


@pytest.mark.parametrize(
    "reason", ["retries_exhausted", "banned_content", "infeasible_config", "resumes_exhausted"]
)
async def test_failing_records_reason_detail_and_end_and_discards_the_candidate(
    reason: str,
    production: Production,
    planning: PhaseDouble,
    seed: Seed,
    session_factory: sessionmaker[Session],
) -> None:
    async def failing_gate(run_id: int, trace: Trace) -> None:
        raise RunStop("failed", reason, "detalle del fallo")

    set_run(session_factory, seed.run_id, phase="gate", chapter=None)
    orchestrator = Orchestrator(production=production, planning=planning, gate=failing_gate)

    await orchestrator.execute(seed.run_id)

    run = get(session_factory, seed.run_id)
    assert (run.status, run.reason, run.reason_detail) == ("failed", reason, "detalle del fallo")
    assert run.finished_at == FINISHED
    assert version_status(session_factory, seed.version_id) == "discarded"
    with unit_of_work(session_factory) as uow, pytest.raises(ResumeRejected):
        resume_run(uow, seed.run_id)
    assert get(session_factory, seed.run_id).status == "failed"


async def test_a_planning_failure_of_010_also_discards_the_candidate(
    production: Production,
    gate: PhaseDouble,
    seed: Seed,
    session_factory: sessionmaker[Session],
) -> None:
    async def failing_planning(run_id: int, trace: Trace) -> None:
        raise RunStop("failed", "retries_exhausted", "outline rechazó los tres planes")

    with session_factory() as session:
        session.execute(delete(Checkpoint).where(Checkpoint.run_id == seed.run_id))
        session.commit()
    set_run(session_factory, seed.run_id, phase=None, chapter=None)
    orchestrator = Orchestrator(production=production, planning=failing_planning, gate=gate)

    await orchestrator.execute(seed.run_id)

    run = get(session_factory, seed.run_id)
    assert (run.status, run.reason) == ("failed", "retries_exhausted")
    assert version_status(session_factory, seed.version_id) == "discarded"
    assert gate.calls == []


async def test_a_chapter_that_exhausts_its_attempts_fails_and_the_worker_takes_the_next(
    production: Production,
    orchestrator: Orchestrator,
    fake: FakeAgent,
    seed: Seed,
    session_factory: sessionmaker[Session],
) -> None:
    set_run(session_factory, seed.run_id, status="queued", phase=None, chapter=None)
    (following,) = queue_others(session_factory, 5)
    worker = make_worker(production, orchestrator)
    script_chapter_failure(fake)

    assert await worker.run_next() == seed.run_id

    run = get(session_factory, seed.run_id)
    assert (run.status, run.reason) == ("failed", "retries_exhausted")
    assert run.reason_detail is not None
    assert "capítulo 1" in run.reason_detail
    assert version_status(session_factory, seed.version_id) == "discarded"
    assert get(session_factory, following).status == "queued"

    script_chapter_failure(fake)
    assert await worker.run_next() == following
    assert get(session_factory, following).status == "failed"


def set_checkpoints(session_factory: sessionmaker[Session], run_id: int, last: int) -> None:
    """Puntos de control 0…`last`: la ejecución sigue en el capítulo `last` + 1."""
    with session_factory() as session:
        run = session.get_one(Run, run_id)
        run.chapter = last + 1
        session.add_all(
            Checkpoint(run_id=run_id, chapter=k, created_at=NOW) for k in range(1, last + 1)
        )
        session.commit()


def chapter_rows(session_factory: sessionmaker[Session], version_id: int, number: int) -> int:
    with session_factory() as session:
        return session.query(Chapter).filter_by(version_id=version_id, number=number).count()


def counted_attempts(session_factory: sessionmaker[Session], run_id: int, chapter: int) -> int:
    with session_factory() as session:
        rows = session.query(Attempt).filter(
            Attempt.run_id == run_id, Attempt.chapter == chapter, Attempt.outcome.is_not(None)
        )
        return rows.count()


@pytest.mark.parametrize(
    ("role", "failure"),
    [
        ("writer", Fail(result=True)),  # también el límite de uso de la suscripción
        ("writer", Fail()),
        ("editor", Fail(result=True)),
    ],
)
async def test_a_provider_error_interrupts_and_does_not_count_as_an_attempt(
    role: str,
    failure: Fail,
    production: Production,
    orchestrator: Orchestrator,
    fake: FakeAgent,
    seed: Seed,
    session_factory: sessionmaker[Session],
) -> None:
    set_run(session_factory, seed.run_id, status="queued", phase=None, chapter=None)
    set_checkpoints(session_factory, seed.run_id, 5)
    (following,) = queue_others(session_factory, 5)
    if role == "writer":
        fake.script("writer", "write", Script(steps=(failure,)))
    else:
        fake.script("writer", "write", writer_script(chapter_call()))
        fake.script("editor", None, Script(steps=(failure,)))
    worker = make_worker(production, orchestrator)

    assert await worker.run_next() == seed.run_id

    run = get(session_factory, seed.run_id)
    assert (run.status, run.reason) == ("interrupted", "provider_error")
    assert counted_attempts(session_factory, seed.run_id, 6) == 0
    assert chapter_rows(session_factory, seed.version_id, 6) == 0
    assert version_status(session_factory, seed.version_id) == "candidate"
    script_chapter_failure(fake)
    assert await worker.run_next() == following

"""Reanudar sigue tras el último punto de control (011-C27)."""

from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    NOW,
    FixedWindows,
    PhaseDouble,
    Seed,
    script_accepted_chapters,
    writer_script,
)

from story_maker.agents.fake import FakeAgent
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import Production
from story_maker.pipeline.runs import resume_run
from story_maker.pipeline.worker import Worker
from story_maker.store.models import Attempt, Checkpoint, Run
from story_maker.store.session import unit_of_work


def interrupt_at(
    session_factory: sessionmaker[Session],
    run_id: int,
    *,
    phase: str,
    chapter: int | None,
    checkpoints: range,
) -> None:
    """La ejecución cayó en `phase` con los puntos de control `checkpoints` y se reanuda."""
    with session_factory() as session:
        session.execute(delete(Checkpoint).where(Checkpoint.run_id == run_id))
        session.add_all(Checkpoint(run_id=run_id, chapter=k, created_at=NOW) for k in checkpoints)
        run = session.get_one(Run, run_id)
        run.status, run.phase, run.chapter = "interrupted", phase, chapter
        run.reason, run.reason_detail = "crash", "el servidor se detuvo"
        session.commit()
    with unit_of_work(session_factory) as uow:
        resume_run(uow, run_id)


def checkpoints(session_factory: sessionmaker[Session], run_id: int) -> list[int]:
    with session_factory() as session:
        rows = session.query(Checkpoint.chapter).filter(Checkpoint.run_id == run_id)
        return sorted(row[0] for row in rows)


def worker_for(production: Production, orchestrator: Orchestrator) -> Worker:
    return Worker(
        production.session_factory,
        orchestrator.execute,
        max_resumes=production.config.max_resumes,
        clock=production.clock,
    )


async def test_fallen_in_planning_before_the_plan_resumes_in_planning(
    production: Production,
    gate: PhaseDouble,
    fake: FakeAgent,
    seed: Seed,
    session_factory: sessionmaker[Session],
) -> None:
    interrupt_at(session_factory, seed.run_id, phase="planning", chapter=None, checkpoints=range(0))
    phases: list[str | None] = []

    def plan(run_id: int) -> None:
        with session_factory() as session:
            phases.append(session.get_one(Run, run_id).phase)
            session.add(Checkpoint(run_id=run_id, chapter=0, created_at=NOW))
            session.commit()

    planning = PhaseDouble(action=plan)
    orchestrator = Orchestrator(production=production, planning=planning, gate=gate)
    script_accepted_chapters(fake, 10)

    assert await worker_for(production, orchestrator).run_next() == seed.run_id

    assert phases == ["planning"]
    assert checkpoints(session_factory, seed.run_id) == list(range(11))


async def test_fallen_right_after_applying_the_plan_resumes_writing_chapter_1_without_planner(
    production: Production,
    orchestrator: Orchestrator,
    planning: PhaseDouble,
    gate: PhaseDouble,
    windows: FixedWindows,
    fake: FakeAgent,
    seed: Seed,
    session_factory: sessionmaker[Session],
) -> None:
    interrupt_at(session_factory, seed.run_id, phase="planning", chapter=None, checkpoints=range(1))
    script_accepted_chapters(fake, 10)

    await worker_for(production, orchestrator).run_next()

    assert planning.calls == []
    assert [chapter for _, chapter in windows.writer_calls] == list(range(1, 11))
    assert checkpoints(session_factory, seed.run_id) == list(range(11))
    assert gate.calls == [seed.run_id]


async def test_fallen_in_chapter_6_redoes_it_from_scratch_with_the_attempts_it_had_left(
    production: Production,
    orchestrator: Orchestrator,
    windows: FixedWindows,
    fake: FakeAgent,
    seed: Seed,
    session_factory: sessionmaker[Session],
) -> None:
    interrupt_at(session_factory, seed.run_id, phase="writing", chapter=6, checkpoints=range(6))
    with session_factory() as session:
        session.add(
            Attempt(run_id=seed.run_id, evaluable="chapter", chapter=6, number=1, outcome="rewrite")
        )
        session.commit()
    fake.script("writer", "write", writer_script())
    fake.script("writer", "rewrite", writer_script())
    fake.script("writer", "rewrite", writer_script())

    await worker_for(production, orchestrator).run_next()

    assert [chapter for _, chapter in windows.writer_calls] == [6]
    assert [s.request.mode for s in fake.sessions] == ["write", "rewrite"]
    with session_factory() as session:
        run = session.get_one(Run, seed.run_id)
        assert (run.status, run.reason) == ("failed", "retries_exhausted")
        numbers = session.query(Attempt.number).filter_by(run_id=seed.run_id, chapter=6)
        assert sorted(row[0] for row in numbers) == [1, 2, 3]
    assert checkpoints(session_factory, seed.run_id) == list(range(6))


async def test_fallen_in_gate_or_rewriting_resumes_in_the_gate_without_rewriting_chapters(
    production: Production,
    orchestrator: Orchestrator,
    planning: PhaseDouble,
    gate: PhaseDouble,
    fake: FakeAgent,
    seed: Seed,
    session_factory: sessionmaker[Session],
) -> None:
    for phase in ("gate", "rewriting"):
        interrupt_at(session_factory, seed.run_id, phase=phase, chapter=None, checkpoints=range(11))
        gate.calls.clear()

        await worker_for(production, orchestrator).run_next()

        assert gate.calls == [seed.run_id]
        assert fake.sessions == []
        assert planning.calls == []
        assert checkpoints(session_factory, seed.run_id) == list(range(11))
        with session_factory() as session:
            assert session.get_one(Run, seed.run_id).phase == "gate"

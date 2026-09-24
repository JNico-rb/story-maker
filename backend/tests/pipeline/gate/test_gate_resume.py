"""012-C22 · Reanudar en `gate` o en `rewriting` repasa el gate sobre la candidata tal como
quedó."""

from __future__ import annotations

import asyncio
import datetime as dt

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import FixedWindows, PhaseDouble, Seed
from tests.pipeline.gate.conftest import (
    PASSED,
    GateKit,
    chapter_hashes,
    evaluation,
    gate_passes,
    run_of,
    script_judges,
    script_rewrites,
    visual_defects,
)

from story_maker.agents.fake import FakeAgent
from story_maker.formal.result import VerifierInterruption
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import Production
from story_maker.pipeline.runs import resume_run
from story_maker.pipeline.worker import Worker
from story_maker.store.models import Checkpoint
from story_maker.store.session import unit_of_work


@pytest.fixture
def orchestrator(production: Production, planning: PhaseDouble, kit: GateKit) -> Orchestrator:
    return Orchestrator(production=production, planning=planning, gate=kit.gate)


@pytest.fixture
def worker(session_factory: sessionmaker[Session], orchestrator: Orchestrator) -> Worker:
    return Worker(
        session_factory,
        orchestrator.execute,
        max_resumes=2,
        clock=lambda: dt.datetime(2026, 9, 24, 14, 0, tzinfo=dt.UTC),
    )


def _resume(session_factory: sessionmaker[Session], run_id: int) -> None:
    with unit_of_work(session_factory) as uow:
        resume_run(uow, run_id)


def _checkpoints(session_factory: sessionmaker[Session], run_id: int) -> list[int]:
    with session_factory() as session:
        rows = session.query(Checkpoint.chapter).filter(Checkpoint.run_id == run_id)
        return sorted(row[0] for row in rows)


def test_a_crash_while_rewriting_resumes_with_a_new_pass_on_the_candidate_as_it_was_left(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    orchestrator: Orchestrator,
    worker: Worker,
    windows: FixedWindows,
    planning: PhaseDouble,
) -> None:
    script_judges(fake, evaluation({"continuidad": 2}, {"continuidad": (2, 5)}), evaluation())
    script_rewrites(fake, 1)
    before = chapter_hashes(session_factory, at_gate.version_id)
    windows.fail_on_chapter = 5  # el proceso muere al empezar a reescribir el 5
    with pytest.raises(KeyError):
        asyncio.run(orchestrator.execute(at_gate.run_id))
    assert run_of(session_factory, at_gate.run_id).phase == "rewriting"
    windows.fail_on_chapter = None
    assert worker.recover() == [at_gate.run_id]
    _resume(session_factory, at_gate.run_id)
    rewritten = chapter_hashes(session_factory, at_gate.version_id)

    asyncio.run(worker.run_next())

    assert gate_passes(session_factory, at_gate.run_id) == [(1, "rewrite"), (2, "accept")]
    assert rewritten[2] != before[2]
    assert rewritten[5] == before[5]
    assert chapter_hashes(session_factory, at_gate.version_id) == rewritten
    writers = [s.request.chapter for s in fake.sessions if s.request.role == "writer"]
    assert writers == [2]
    assert planning.calls == []
    assert _checkpoints(session_factory, at_gate.run_id) == list(range(11))
    assert run_of(session_factory, at_gate.run_id).status == "published"


def test_an_unreachable_verifier_in_pass_2_repeats_pass_2_on_resume(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    orchestrator: Orchestrator,
    worker: Worker,
    planning: PhaseDouble,
) -> None:
    kit.visual.outcomes.append(visual_defects(3))
    kit.lean.outcomes.extend([PASSED, VerifierInterruption("verifier_unreachable")])
    script_judges(fake, evaluation(), evaluation(), evaluation())
    script_rewrites(fake, 1)

    asyncio.run(orchestrator.execute(at_gate.run_id))
    stopped = run_of(session_factory, at_gate.run_id)
    assert (stopped.status, stopped.reason) == ("interrupted", "verifier_unreachable")
    assert gate_passes(session_factory, at_gate.run_id) == [(1, "rewrite")]
    rewritten = chapter_hashes(session_factory, at_gate.version_id)
    _resume(session_factory, at_gate.run_id)

    asyncio.run(worker.run_next())

    assert gate_passes(session_factory, at_gate.run_id) == [(1, "rewrite"), (2, "accept")]
    assert chapter_hashes(session_factory, at_gate.version_id) == rewritten
    assert kit.lean.calls == [at_gate.run_id] * 3
    writers = [s.request.chapter for s in fake.sessions if s.request.role == "writer"]
    assert writers == [3]
    assert planning.calls == []
    assert run_of(session_factory, at_gate.run_id).status == "published"

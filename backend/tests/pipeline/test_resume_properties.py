"""`ReanudacionSinDuplicarNiPerder` y `ReintentosAcotados` (011-I2, I3): caídas generadas en
cada fase, dentro de `max_resumes`, seguidas de reanudaciones."""

from __future__ import annotations

import asyncio
import datetime as dt
from collections.abc import Callable
from pathlib import Path
from typing import Literal

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    SuccessorCards,
    chapter_call,
    editor_script,
    fresh_database,
    make_production,
    review,
    seed_candidate,
    seed_novel,
    seed_run,
    seed_user,
    writer_script,
)

from story_maker.agents.fake import Fail, FakeAgent, Script
from story_maker.config import Config
from story_maker.observability.port import Trace
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.runs import RunStop, resume_run
from story_maker.pipeline.worker import Worker
from story_maker.store.models import Attempt, Chapter, Checkpoint, Run
from story_maker.store.session import (
    UnitOfWork,
    unit_of_work,
)

PROPERTY = settings(
    max_examples=25, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
NOW = dt.datetime(2026, 9, 24, 12, 0)

Where = Literal["planning", "writer", "editor", "acceptance", "gate"]
Crash = tuple[Where, int]

crashes = st.lists(
    st.one_of(
        st.tuples(st.sampled_from(["planning", "gate"]), st.just(0)),
        st.tuples(
            st.sampled_from(["writer", "editor", "acceptance"]),
            st.integers(min_value=1, max_value=10),
        ),
    ),
    max_size=2,
    unique=True,
).map(lambda cs: sorted(cs, key=order))


def order(crash: Crash) -> tuple[int, int]:
    where, chapter = crash
    stage = {"planning": 0, "gate": 11}.get(where, chapter)
    return stage, ["planning", "writer", "editor", "acceptance", "gate"].index(where)


class FlakyCards:
    """La sincronización de tarjetas falla en las llamadas `failing`: la transacción de
    aceptación se deshace y la ejecución cae con `crash`."""

    def __init__(self, failing: set[int]) -> None:
        self.inner = SuccessorCards()
        self.failing = failing
        self.calls = 0

    def __call__(self, uow: UnitOfWork, version_id: int) -> None:
        self.calls += 1
        if self.calls in self.failing:
            raise RuntimeError("se cayó la escritura de las tarjetas")
        self.inner(uow, version_id)


def script(fake: FakeAgent, plan: list[Crash]) -> set[int]:
    """Guiones en el orden en que se piden; devuelve qué aceptaciones fallan."""
    accepts = 0
    failing: set[int] = set()
    for chapter in range(1, 11):
        for where, at in plan:
            if at != chapter:
                continue
            if where == "writer":
                fake.script("writer", "write", Script(steps=(Fail(result=True),)))
                continue
            fake.script("writer", "write", writer_script(chapter_call()))
            if where == "editor":
                fake.script("editor", None, Script(steps=(Fail(result=True),)))
                continue
            fake.script("editor", None, editor_script(review()))
            accepts += 1
            failing.add(accepts)
        fake.script("writer", "write", writer_script(chapter_call()))
        fake.script("editor", None, editor_script(review()))
        accepts += 1
    return failing


class CrashingPhase:
    """Planificación o gate: cae la primera vez si el plan lo pide; si no, cumple su fase."""

    def __init__(
        self, where: Where, plan: list[Crash], action: Callable[[int], None] | None = None
    ) -> None:
        self.where = where
        self.falls = (where, 0) in plan
        self.action = action
        self.calls: list[int] = []

    async def __call__(self, run_id: int, trace: Trace) -> None:
        self.calls.append(run_id)
        if self.falls:
            self.falls = False
            raise RunStop("interrupted", "crash", f"cayó en {self.where}")
        if self.action is not None:
            self.action(run_id)


@PROPERTY
@given(plan=crashes)
def test_resuming_after_any_crashes_neither_duplicates_nor_loses_and_retries_stay_bounded(
    plan: list[Crash],
    config: Config,
    workspace: Path,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    with fresh_database(tmp_path_factory.mktemp("db")) as session_factory:
        run_id, version_id = setup(session_factory)
        fake = FakeAgent()
        cards = FlakyCards(script(fake, plan))
        planning, gate, worker = build(
            session_factory, config, workspace, fake, cards, plan, run_id
        )

        asyncio.run(drive(worker, session_factory, run_id))

        with session_factory() as session:
            run = session.get_one(Run, run_id)
            assert run.status == "running"
            assert run.resumes == len(plan)
            points = [row[0] for row in session.query(Checkpoint.chapter).filter_by(run_id=run_id)]
            assert sorted(points) == list(range(11))
            chapters = [
                row[0] for row in session.query(Chapter.number).filter_by(version_id=version_id)
            ]
            assert sorted(chapters) == list(range(1, 11))
            counted = session.query(Attempt).filter(
                Attempt.run_id == run_id, Attempt.outcome.is_not(None)
            )
            per_chapter: dict[int | None, int] = {}
            for attempt in counted:
                per_chapter[attempt.chapter] = per_chapter.get(attempt.chapter, 0) + 1
            assert per_chapter == dict.fromkeys(range(1, 11), 1)
        assert len(planning.calls) == 1 + sum(1 for w, _ in plan if w == "planning")
        assert len(gate.calls) == 1 + sum(1 for w, _ in plan if w == "gate")


def setup(session_factory: sessionmaker[Session]) -> tuple[int, int]:
    with session_factory() as session:
        user = seed_user(session)
        novel = seed_novel(session, user.id)
        version, *_ = seed_candidate(session, novel.id)
        run = seed_run(
            session,
            novel.id,
            status="queued",
            phase=None,
            chapter=None,
            candidate=version.id,
            checkpoints=(),
        )
        session.commit()
        return run.id, version.id


def build(
    session_factory: sessionmaker[Session],
    config: Config,
    workspace: Path,
    fake: FakeAgent,
    cards: FlakyCards,
    plan: list[Crash],
    run_id: int,
) -> tuple[CrashingPhase, CrashingPhase, Worker]:
    with session_factory() as session:
        novel_id = session.get_one(Run, run_id).novel_id
    production = make_production(session_factory, config, workspace, fake, cards, novel_id)

    def apply_plan(rid: int) -> None:
        with session_factory() as session:
            session.add(Checkpoint(run_id=rid, chapter=0, created_at=NOW))
            session.commit()

    planning = CrashingPhase("planning", plan, apply_plan)
    gate = CrashingPhase("gate", plan)
    orchestrator = Orchestrator(production=production, planning=planning, gate=gate)
    worker = Worker(
        session_factory,
        orchestrator.execute,
        max_resumes=config.max_resumes,
        clock=production.clock,
    )
    return planning, gate, worker


async def drive(worker: Worker, session_factory: sessionmaker[Session], run_id: int) -> None:
    """El worker la lleva; cada vez que cae, se reanuda, hasta que queda en el gate."""
    for _ in range(4):
        await worker.run_next()
        with session_factory() as session:
            status = session.get_one(Run, run_id).status
        if status != "interrupted":
            return
        with unit_of_work(session_factory) as uow:
            resume_run(uow, run_id)

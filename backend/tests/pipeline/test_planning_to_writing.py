"""De la planificación a la escritura (011-C05)."""

from __future__ import annotations

import dataclasses

from sqlalchemy import delete
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    FixedWindows,
    PhaseDouble,
    Seed,
    script_accepted_chapters,
)

from story_maker.agents.fake import FakeAgent
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import Production
from story_maker.pipeline.windows import WriterWindow
from story_maker.pipeline.worker import Worker
from story_maker.store.models import Checkpoint, Run

State = tuple[str, str | None, int | None]


def state_of(session: Session, run_id: int) -> State:
    run = session.get_one(Run, run_id)
    return run.status, run.phase, run.chapter


@dataclasses.dataclass
class WatchingWindows(FixedWindows):
    """Registra el estado de la ejecución al ensamblar la ventana del writer de cada capítulo."""

    run_id: int = 0
    states: dict[int, State] = dataclasses.field(default_factory=dict)

    def writer(self, session: Session, version_id: int, chapter: int) -> WriterWindow:
        self.states.setdefault(chapter, state_of(session, self.run_id))
        return super().writer(session, version_id, chapter)


async def test_a_taken_generation_plans_and_then_writes_from_chapter_1_without_another_planner(
    production: Production,
    gate: PhaseDouble,
    fake: FakeAgent,
    seed: Seed,
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        session.execute(delete(Checkpoint).where(Checkpoint.run_id == seed.run_id))
        run = session.get_one(Run, seed.run_id)
        run.status, run.phase, run.chapter = "queued", None, None
        session.commit()
    at_planning: list[State] = []

    def plan(run_id: int) -> None:
        with session_factory() as session:
            at_planning.append(state_of(session, run_id))
            session.add(Checkpoint(run_id=run_id, chapter=0, created_at=run.created_at))
            session.commit()

    planning = PhaseDouble(action=plan)
    windows = WatchingWindows(run_id=seed.run_id)
    production = dataclasses.replace(production, windows=windows)
    orchestrator = Orchestrator(production=production, planning=planning, gate=gate)
    worker = Worker(
        session_factory,
        orchestrator.execute,
        max_resumes=production.config.max_resumes,
        clock=production.clock,
    )
    script_accepted_chapters(fake, 10)

    assert await worker.run_next() == seed.run_id

    assert at_planning == [("running", "planning", None)]
    assert planning.calls == [seed.run_id]
    assert windows.states[1] == ("running", "writing", 1)
    assert sorted(windows.states) == list(range(1, 11))
    assert "planner" not in {s.request.role for s in fake.sessions}
    assert gate.calls == [seed.run_id]

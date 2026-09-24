"""012-I2 · `ReintentosAcotados` en el gate: las pasadas contadas de una ejecución nunca superan
1 + `max_retries.gate_cycles`, ni los intentos de un capítulo en un ciclo, 1 +
`max_retries.chapter`. Propiedad sobre secuencias generadas de resultados de los dobles, con
interrupciones intercaladas y reanudaciones."""

from __future__ import annotations

import asyncio
import dataclasses
from pathlib import Path
from typing import Literal

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    PhaseDouble,
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
from tests.pipeline.gate.conftest import (
    PASSED,
    evaluation,
    make_kit,
    script_judges,
    seed_chapters,
    seed_world,
    visual_defects,
)

from story_maker.agents.fake import FakeAgent
from story_maker.config import Config
from story_maker.formal.result import VerifierInterruption
from story_maker.pipeline.gate.phase import VisualReviewOutcome
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.runs import resume_run
from story_maker.pipeline.worker import Worker
from story_maker.store.models import Attempt, Run
from story_maker.store.session import unit_of_work

PROPERTY = settings(
    max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
Pass = Literal["clean", "defect", "interrupt"]
SPARE = 40


def setup(session_factory: sessionmaker[Session]) -> tuple[int, int]:
    """Una candidata con sus 10 capítulos aceptados y la ejecución `running` en el gate."""
    with session_factory() as session:
        user = seed_user(session)
        novel = seed_novel(session, user.id)
        version, *_ = seed_candidate(session, novel.id)
        seed_world(session, version.id)
        seed_chapters(session, version.id)
        run = seed_run(
            session,
            novel.id,
            phase="gate",
            chapter=None,
            candidate=version.id,
            checkpoints=range(11),
        )
        session.commit()
        return run.id, novel.id


def script(fake: FakeAgent, verdicts: list[bool]) -> None:
    """Los intentos de reescritura, en el orden en que se piden: aceptado o rechazado."""
    for accepted in [*verdicts, *([True] * SPARE)]:
        fake.script("writer", "rewrite", writer_script(chapter_call(title="Reescrito")))
        fake.script("editor", None, editor_script(review(4 if accepted else 2)))


@PROPERTY
@given(
    cycles=st.integers(min_value=0, max_value=2),
    chapter_retries=st.integers(min_value=0, max_value=1),
    passes=st.lists(st.sampled_from(["clean", "defect", "interrupt"]), max_size=6),
    verdicts=st.lists(st.booleans(), max_size=8),
)
def test_counted_passes_and_chapter_attempts_per_cycle_stay_bounded(
    cycles: int,
    chapter_retries: int,
    passes: list[Pass],
    verdicts: list[bool],
    config: Config,
    workspace: Path,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    config = dataclasses.replace(
        config,
        max_retries={**config.max_retries, "gate_cycles": cycles, "chapter": chapter_retries},
        max_resumes=SPARE,
    )
    directory = tmp_path_factory.mktemp("db")
    with fresh_database(directory) as session_factory:
        run_id, novel_id = setup(session_factory)
        fake = FakeAgent()
        production = make_production(
            session_factory, config, workspace, fake, SuccessorCards(), novel_id
        )
        kit = make_kit(production, session_factory, directory)
        for kind in passes:
            kit.lean.outcomes.append(
                VerifierInterruption("verifier_unreachable") if kind == "interrupt" else PASSED
            )
            if kind != "interrupt":
                kit.visual.outcomes.append(
                    visual_defects(3) if kind == "defect" else VisualReviewOutcome()
                )
        script_judges(fake, *(evaluation() for _ in range(len(passes) + SPARE)))
        script(fake, verdicts)
        orchestrator = Orchestrator(production=production, planning=PhaseDouble(), gate=kit.gate)
        worker = Worker(
            session_factory, orchestrator.execute, max_resumes=SPARE, clock=production.clock
        )

        asyncio.run(orchestrator.execute(run_id))
        for _ in range(len(passes) + 1):
            with session_factory() as session:
                if session.get_one(Run, run_id).status != "interrupted":
                    break
            with unit_of_work(session_factory) as uow:
                resume_run(uow, run_id)
            asyncio.run(worker.run_next())

        with session_factory() as session:
            assert session.get_one(Run, run_id).status in ("published", "failed")
            counted = (
                session.query(Attempt)
                .filter(Attempt.run_id == run_id, Attempt.outcome.is_not(None))
                .all()
            )
            gate = [a for a in counted if a.evaluable == "gate_cycle"]
            assert 1 <= len(gate) <= 1 + cycles
            per_cycle: dict[tuple[int | None, int | None], int] = {}
            for attempt in counted:
                if attempt.evaluable == "chapter":
                    key = (attempt.chapter, attempt.gate_cycle)
                    per_cycle[key] = per_cycle.get(key, 0) + 1
            assert all(n <= 1 + chapter_retries for n in per_cycle.values())

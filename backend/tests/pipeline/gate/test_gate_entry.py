"""012-C1 · La candidata entra al gate con sus 10 capítulos aceptados."""

from __future__ import annotations

import asyncio
from typing import Any, cast

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    NOW,
    PhaseDouble,
    Seed,
    chapter_call,
    editor_script,
    review,
    writer_script,
)
from tests.pipeline.gate.conftest import (
    GateKit,
    evaluation,
    gate_passes,
    results,
    run_of,
    script_judges,
    seed_chapters,
    seed_world,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Trace
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import ChapterProducer, Production
from story_maker.store.models import Chapter, Checkpoint, Run


def _accepted_up_to(
    session_factory: sessionmaker[Session], seed: Seed, last: int, *, chapters: int
) -> None:
    """La candidata con `chapters` capítulos y la ejecución en `writing` tras aceptar `last`."""
    with session_factory() as session:
        seed_world(session, seed.version_id)
        seed_chapters(session, seed.version_id)
        session.query(Chapter).filter(
            Chapter.version_id == seed.version_id, Chapter.number > chapters
        ).delete()
        for k in range(1, last + 1):
            session.add(Checkpoint(run_id=seed.run_id, chapter=k, created_at=NOW))
        run = session.get(Run, seed.run_id)
        assert run is not None
        run.phase, run.chapter = "writing", last + 1
        session.commit()


def test_accepting_chapter_10_moves_to_gate_and_opens_pass_1(
    session_factory: sessionmaker[Session],
    seed: Seed,
    fake: FakeAgent,
    production: Production,
    kit: GateKit,
    planning: PhaseDouble,
) -> None:
    _accepted_up_to(session_factory, seed, 9, chapters=9)
    fake.script("writer", "write", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(review()))
    script_judges(fake, evaluation())

    orchestrator = Orchestrator(production=production, planning=planning, gate=kit.gate)
    asyncio.run(orchestrator.execute(seed.run_id))

    run = run_of(session_factory, seed.run_id)
    assert run.phase == "gate"
    assert gate_passes(session_factory, seed.run_id) == [(1, "accept")]
    cycles = {
        cast(dict[str, Any], r.detail)["gate_cycle"] for r in results(session_factory, seed.run_id)
    }
    assert cycles == {1}


def test_accepting_chapter_9_stays_in_writing_and_runs_no_gate_validator(
    session_factory: sessionmaker[Session],
    seed: Seed,
    fake: FakeAgent,
    producer: ChapterProducer,
    trace: Trace,
    kit: GateKit,
) -> None:
    _accepted_up_to(session_factory, seed, 8, chapters=8)
    fake.script("writer", "write", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(review()))

    asyncio.run(producer.produce_chapter(seed.run_id, 9, trace))

    run = run_of(session_factory, seed.run_id)
    assert (run.phase, run.chapter) == ("writing", 10)
    assert results(session_factory, seed.run_id) == []
    assert gate_passes(session_factory, seed.run_id) == []
    assert kit.lean.calls == []
    assert kit.pdf.calls == []


def test_the_gate_never_runs_on_a_candidate_without_its_10_chapters(
    session_factory: sessionmaker[Session], seed: Seed, kit: GateKit, trace: Trace
) -> None:
    _accepted_up_to(session_factory, seed, 9, chapters=9)

    with pytest.raises(RuntimeError, match="10 capítulos"):
        asyncio.run(kit.gate(seed.run_id, trace))

    assert results(session_factory, seed.run_id) == []
    assert gate_passes(session_factory, seed.run_id) == []

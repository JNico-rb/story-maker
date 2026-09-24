"""Una generación nueva tras un fallo tiene su propia candidata (010-C28)."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.planning.test_candidate import reference_brief

from story_maker.pipeline.planning.candidate import start_generation_phase
from story_maker.store.models import Character, Run, Version
from story_maker.store.session import unit_of_work
from story_maker.store.versions import discard

NOW = dt.datetime(2026, 9, 24, 12, 0)


async def test_a_new_generation_gets_its_own_candidate_after_a_previous_failure(
    session_factory: sessionmaker[Session], run_id: int, novel_id: int
) -> None:
    version_a = start_generation_phase(
        session_factory, run_id, novel_id, reference_brief(), now=NOW
    )
    with unit_of_work(session_factory) as uow:
        run_a = uow.session.get(Run, run_id)
        assert run_a is not None
        run_a.status = "failed"
        run_a.reason = "retries_exhausted"
        run_a.finished_at = NOW
        discard(uow, version_a.id)

    with unit_of_work(session_factory) as uow:
        run_b = Run(
            novel_id=novel_id, type="generation", status="running", resumes=0, created_at=NOW
        )
        uow.add(run_b)
    run_b_id = run_b.id

    version_b = start_generation_phase(
        session_factory, run_b_id, novel_id, reference_brief(), now=NOW
    )

    assert version_b.id != version_a.id
    with session_factory() as session:
        a = session.get(Version, version_a.id)
        b = session.get(Version, version_b.id)
        assert a is not None
        assert b is not None
        assert a.status == "discarded"
        assert b.status == "candidate"

        a_characters = sorted(
            c.canonical_name for c in session.scalars(select(Character).filter_by(version_id=a.id))
        )
        b_characters = sorted(
            c.canonical_name for c in session.scalars(select(Character).filter_by(version_id=b.id))
        )
        assert a_characters == b_characters == ["Marta", "Rosa", "Toby"]

        run_b_row = session.get(Run, run_b_id)
        assert run_b_row is not None
        assert run_b_row.candidate_version_id == version_b.id

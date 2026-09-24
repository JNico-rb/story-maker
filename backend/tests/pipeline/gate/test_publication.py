"""012-C23 · La publicación es una transacción."""

from __future__ import annotations

import asyncio

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import NOW, Seed, seed_novel
from tests.pipeline.gate.conftest import (
    GateKit,
    evaluation,
    gate_passes,
    run_of,
    script_judges,
    seed_change_over_v3,
    version_of,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Trace
from story_maker.pipeline.gate import publication
from story_maker.pipeline.runs import RunStop
from story_maker.store.models import ChangeRequest, ManualEdit, Run, Version


def test_a_change_candidate_over_v3_publishes_as_v4_with_its_changed_chapters_and_applies_it(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    change = seed_change_over_v3(session_factory, at_gate)
    script_judges(fake, evaluation())

    asyncio.run(kit.gate(change.run_id, trace))

    version = version_of(session_factory, change.candidate_id)
    assert (version.status, version.number) == ("published", 4)
    assert version.published_at is not None
    assert version.changed_chapters == [2, 5]
    assert version.pdf_path == kit.pdf.path
    assert run_of(session_factory, change.run_id).status == "published"
    with session_factory() as session:
        assert session.get_one(ChangeRequest, change.request_id).status == "applied"
    assert gate_passes(session_factory, change.run_id) == [(1, "accept")]


def test_the_first_generation_of_a_novel_is_v1_with_no_changed_chapters_whatever_other_novels_have(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    with session_factory() as session:
        other = seed_novel(session, at_gate.user_id)
        for number in (1, 2, 3):
            session.add(
                Version(
                    novel_id=other.id,
                    status="published",
                    number=number,
                    changed_chapters=[],
                    created_at=NOW,
                    published_at=NOW,
                )
            )
        session.commit()
    script_judges(fake, evaluation())

    asyncio.run(kit.gate(at_gate.run_id, trace))

    version = version_of(session_factory, at_gate.version_id)
    assert (version.status, version.number, version.changed_chapters) == ("published", 1, [])
    assert version.published_at is not None
    assert version.pdf_path == kit.pdf.path


def test_a_manual_edit_candidate_publishes_and_its_edit_is_applied(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    change = seed_change_over_v3(session_factory, at_gate)
    with session_factory() as session:
        session.query(ChangeRequest).delete()
        session.get_one(Run, change.run_id).type = "manual_edit"
        edit = ManualEdit(
            novel_id=at_gate.novel_id,
            base_version_id=change.base_id,
            chapter=2,
            text="texto editado",
            status="queued",
            run_id=change.run_id,
            created_at=NOW,
        )
        session.add(edit)
        session.commit()
        edit_id = edit.id
    script_judges(fake, evaluation())

    asyncio.run(kit.gate(change.run_id, trace))

    assert version_of(session_factory, change.candidate_id).number == 4
    assert run_of(session_factory, change.run_id).status == "published"
    with session_factory() as session:
        assert session.get_one(ManualEdit, edit_id).status == "applied"


def test_a_failure_inside_the_publication_transaction_leaves_nothing_of_it_written(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    change = seed_change_over_v3(session_factory, at_gate)
    script_judges(fake, evaluation())

    def broken(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("disco lleno")

    monkeypatch.setattr(publication, "mark_applied", broken)

    with pytest.raises(RunStop) as stop:
        asyncio.run(kit.gate(change.run_id, trace))

    assert (stop.value.status, stop.value.reason) == ("interrupted", "crash")
    version = version_of(session_factory, change.candidate_id)
    assert (version.status, version.number, version.published_at) == ("candidate", None, None)
    assert (version.changed_chapters, version.pdf_path) == ([], None)
    assert run_of(session_factory, change.run_id).status == "running"
    with session_factory() as session:
        assert session.get_one(ChangeRequest, change.request_id).status == "confirmed"
    assert gate_passes(session_factory, change.run_id) == []

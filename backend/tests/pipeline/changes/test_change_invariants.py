"""Invariantes de la ejecución de cambio sobre varias versiones y varias solicitudes: 014-I7
(`VersionAnteriorConservada`), 014-I8 (`VersionesLineales`) y 014-I10
(`ReanudacionSinDuplicarNiPerder`)."""

from __future__ import annotations

import dataclasses

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.changes.conftest import (
    V1,
    CrashingWindows,
    confirm,
    crash_and_restart,
    new_trait,
    rename_toby,
    request_of,
    resume,
    run_of,
    script_judge,
    script_revisions,
    version_fingerprint,
    versions,
)
from tests.pipeline.gate.conftest import GateKit

from story_maker.agents.fake import FakeAgent
from story_maker.pipeline.gate.phase import PdfOutcome
from story_maker.pipeline.worker import Worker
from story_maker.store.models import ChangeRequest, Character, Checkpoint


def _on(session_factory: sessionmaker[Session], v1: V1, version_id: int) -> V1:
    """Los ids de `v1` que usa una propuesta, traducidos a los de la versión `version_id`."""
    with session_factory() as session:
        dog = (
            session.query(Character)
            .filter(Character.version_id == version_id, Character.canonical_name != "Marta")
            .one()
        )
    return dataclasses.replace(v1, toby_id=dog.id)


def _ordered_checkpoints(session_factory: sessionmaker[Session], run_id: int) -> list[int]:
    with session_factory() as session:
        rows = session.query(Checkpoint.chapter).filter(Checkpoint.run_id == run_id)
        return [row[0] for row in rows.order_by(Checkpoint.id)]


async def test_a_change_never_modifies_any_published_version_whether_it_publishes_or_fails(
    session_factory: sessionmaker[Session],
    v1: V1,
    fake: FakeAgent,
    kit: GateKit,
    worker: Worker,
) -> None:
    confirm(session_factory, v1.novel_id, v1.v1_id, rename_toby(v1))
    script_revisions(fake, 3)
    script_judge(fake)
    await worker.run_next()
    v2 = versions(session_factory, v1.novel_id)[-1]
    published = {v: version_fingerprint(session_factory, v) for v in (v1.v1_id, v2.id)}

    failing = confirm(
        session_factory, v1.novel_id, v2.id, new_trait(_on(session_factory, v1, v2.id))
    )
    script_judge(fake)
    kit.pdf.outcomes.append(PdfOutcome(None, detail="Edge no arrancó"))
    await worker.run_next()
    assert run_of(session_factory, failing.run_id).status == "failed"
    assert {v: version_fingerprint(session_factory, v) for v in published} == published

    passing = confirm(
        session_factory, v1.novel_id, v2.id, new_trait(_on(session_factory, v1, v2.id))
    )
    script_judge(fake)
    await worker.run_next()
    assert run_of(session_factory, passing.run_id).status == "published"
    assert {v: version_fingerprint(session_factory, v) for v in published} == published


async def test_history_stays_linear_and_every_confirmed_request_ends_applied_or_rejected(
    session_factory: sessionmaker[Session],
    v1: V1,
    fake: FakeAgent,
    worker: Worker,
    windows: CrashingWindows,
) -> None:
    crashed = confirm(session_factory, v1.novel_id, v1.v1_id, rename_toby(v1))
    over_v1 = confirm(session_factory, v1.novel_id, v1.v1_id, new_trait(v1))
    late = confirm(session_factory, v1.novel_id, v1.v1_id, new_trait(v1, "odia la lluvia"))
    windows.crash_at = 5
    script_revisions(fake, 1)
    await crash_and_restart(worker)
    script_judge(fake)
    while await worker.run_next() is not None:
        pass
    resume(session_factory, crashed.run_id)
    await worker.run_next()
    v2 = versions(session_factory, v1.novel_id)[-1]
    over_v2 = confirm(
        session_factory, v1.novel_id, v2.id, new_trait(_on(session_factory, v1, v2.id))
    )
    script_judge(fake)
    await worker.run_next()

    published = [v for v in versions(session_factory, v1.novel_id) if v.status == "published"]
    assert [(v.number, v.base_version_id) for v in published] == [
        (1, None),
        (2, v1.v1_id),
        (3, published[1].id),
    ]
    statuses = {
        c.request_id: request_of(session_factory, c.request_id).status
        for c in (crashed, over_v1, late, over_v2)
    }
    assert statuses == {
        crashed.request_id: "rejected",
        over_v1.request_id: "applied",
        late.request_id: "rejected",
        over_v2.request_id: "applied",
    }
    for c in (crashed, late):
        assert run_of(session_factory, c.run_id).reason == "stale_base"
    with session_factory() as session:
        assert {r.status for r in session.query(ChangeRequest)} <= {"applied", "rejected"}


@pytest.mark.parametrize(("crash_at", "before"), [(2, [0]), (5, [0, 2]), (7, [0, 2, 5])])
async def test_checkpoints_are_0_and_an_ordered_prefix_of_the_affected_across_a_resume(
    crash_at: int,
    before: list[int],
    session_factory: sessionmaker[Session],
    v1: V1,
    fake: FakeAgent,
    worker: Worker,
    windows: CrashingWindows,
) -> None:
    confirmed = confirm(session_factory, v1.novel_id, v1.v1_id, rename_toby(v1))
    windows.crash_at = crash_at
    script_revisions(fake, 3)
    script_judge(fake)
    await crash_and_restart(worker)
    assert _ordered_checkpoints(session_factory, confirmed.run_id) == before

    resume(session_factory, confirmed.run_id)
    await worker.run_next()

    assert _ordered_checkpoints(session_factory, confirmed.run_id) == [0, 2, 5, 7]
    writers = [s.request.chapter for s in fake.sessions if s.request.role == "writer"]
    assert writers == [2, 5, 7]
    assert run_of(session_factory, confirmed.run_id).status == "published"

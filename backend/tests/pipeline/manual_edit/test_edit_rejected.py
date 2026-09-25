"""019-C22 y 019-C23 · En el capítulo editado bloquean los validadores deterministas y el gate:
la ejecución termina `failed` con `edit_rejected`, sin reescribir nada, y la edición `rejected`."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.manual_edit.conftest import N
from tests.pipeline.manual_edit.test_edit_run import edit_of, queue_edit, renamed, run_of

from story_maker.agents.fake import FakeAgent
from story_maker.domain.banned_terms import normalize_token
from story_maker.pipeline.report import build_report
from story_maker.pipeline.worker import Worker
from story_maker.store.models import AuditLog, BannedTerm, Run, Version


def _ban(session_factory: sessionmaker[Session], user_id: int, term: str) -> None:
    with session_factory() as session:
        session.add(
            BannedTerm(
                level="user",
                term=term,
                type="word",
                keywords=None,
                normalized=normalize_token(term),
                user_id=user_id,
            )
        )
        session.commit()


def _report(session_factory: sessionmaker[Session], run_id: int) -> dict[str, Any]:
    with session_factory() as session:
        return build_report(session, session.get_one(Run, run_id))


def assert_rejected_and_v1_current(
    session_factory: sessionmaker[Session], n: N, run_id: int, reason: str = "edit_rejected"
) -> Run:
    run = run_of(session_factory, run_id)
    assert (run.status, run.reason) == ("failed", reason), run.reason_detail
    assert edit_of(session_factory, run_id).status == "rejected"
    with session_factory() as session:
        if run.candidate_version_id is not None:
            assert session.get_one(Version, run.candidate_version_id).status == "discarded"
        published = session.query(Version).filter_by(novel_id=n.novel_id, status="published")
        assert [v.id for v in published] == [n.v1_id]
    return run


async def test_a_banned_term_added_before_the_run_starts_rejects_the_edit_without_any_role(
    n: N, fake: FakeAgent, worker: Worker, session_factory: sessionmaker[Session]
) -> None:
    run_id = queue_edit(session_factory, n, renamed(session_factory, n))
    _ban(session_factory, n.user_a, "Nala")

    await worker.run_next()

    assert_rejected_and_v1_current(session_factory, n, run_id)
    assert fake.sessions == []
    with session_factory() as session:
        denials = session.query(AuditLog).filter_by(
            origin="manual_edit", decision="deny", run_id=run_id
        )
        (deny,) = denials
        assert (deny.user_id, deny.novel_id) == (n.user_a, n.novel_id)
    unresolved = _report(session_factory, run_id)["unresolved"]
    assert any(
        d["chapter"] == 3 and d["validator"] == "palabras-prohibidas" and "Nala" in d["message"]
        for d in unresolved
    )

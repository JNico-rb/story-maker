"""019-C21 · Los hechos cambiados inválidos vuelven al editor: error en su sesión, intento del
capítulo editado y, al agotarse, `retries_exhausted` con la edición `rejected`."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import editor_script
from tests.pipeline.gate.conftest import evaluation, judge_script
from tests.pipeline.manual_edit.conftest import N
from tests.pipeline.manual_edit.test_edit_run import (
    attempts,
    candidate_fact,
    edit_of,
    edited_review,
    queue_edit,
    rename_review,
    renamed,
    run_of,
    script_revisions,
)

from story_maker.agents.fake import FakeAgent
from story_maker.pipeline.worker import Worker
from story_maker.store.models import AuditLog, Version


def _invalid_reviews(session_factory: sessionmaker[Session], n: N) -> list[dict[str, Any]]:
    """Un hecho que no existe, el nombre del perro con el valor que ya tiene y el valor nuevo
    «Jorge», prohibida de nivel `novel`."""
    name = candidate_fact(session_factory, n.toby_name, n)
    return [
        edited_review(session_factory, n, changed_facts=[{"fact_id": 99_999, "new_value": "Nala"}]),
        edited_review(session_factory, n, changed_facts=[{"fact_id": name, "new_value": "Toby"}]),
        edited_review(session_factory, n, changed_facts=[{"fact_id": name, "new_value": "Jorge"}]),
    ]


def _denials(session_factory: sessionmaker[Session], run_id: int) -> list[AuditLog]:
    with session_factory() as session:
        rows = session.query(AuditLog).filter_by(
            origin="manual_edit", decision="deny", run_id=run_id
        )
        return list(rows)


async def test_invalid_changed_facts_return_to_the_editor_as_errors_and_count_as_attempts(
    n: N, fake: FakeAgent, worker: Worker, session_factory: sessionmaker[Session]
) -> None:
    run_id = queue_edit(session_factory, n, renamed(session_factory, n))
    invalid = _invalid_reviews(session_factory, n)
    fake.script("editor", None, editor_script(*invalid, rename_review(session_factory, n)))
    script_revisions(fake, 2)
    fake.script("judge", None, judge_script(evaluation(4)))

    await worker.run_next()

    run = run_of(session_factory, run_id)
    assert run.status == "published", run.reason_detail
    (editor, *_) = fake.sessions
    assert editor.request.chapter == 3
    assert "Hecho inexistente" in editor.reads[0]
    assert "no cambia nada" in editor.reads[1]
    assert "Prohibida" in editor.reads[2]
    assert "Jorge" in editor.reads[2]
    assert attempts(session_factory, run_id, 3) == [
        (1, "rewrite"),
        (2, "rewrite"),
        (3, "rewrite"),
        (4, "accept"),
    ]
    (deny,) = _denials(session_factory, run_id)
    assert (deny.user_id, deny.novel_id) == (n.user_a, n.novel_id)
    assert edit_of(session_factory, run_id).status == "applied"


async def test_only_invalid_changed_facts_exhaust_the_attempts_and_reject_the_edit(
    n: N, fake: FakeAgent, worker: Worker, session_factory: sessionmaker[Session]
) -> None:
    run_id = queue_edit(session_factory, n, renamed(session_factory, n))
    invalid = _invalid_reviews(session_factory, n)
    fake.script("editor", None, editor_script(*invalid, invalid[0]))

    await worker.run_next()

    run = run_of(session_factory, run_id)
    assert (run.status, run.reason) == ("failed", "retries_exhausted")
    assert [s.request.role for s in fake.sessions] == ["editor"]
    assert [o for _, o in attempts(session_factory, run_id, 3)] == ["rewrite"] * 3 + ["fail"]
    assert edit_of(session_factory, run_id).status == "rejected"
    with session_factory() as session:
        candidate = session.get_one(Version, run.candidate_version_id)
        assert candidate.status == "discarded"
        published = session.query(Version).filter_by(novel_id=n.novel_id, status="published")
        assert [v.number for v in published] == [1]

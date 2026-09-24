"""014-C10 — Confirmar con el código encola una ejecución de cambio con su versión base."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import FakeAgent
from story_maker.pipeline.runs import queued_runs
from story_maker.store import models
from story_maker.store.session import unit_of_work

from .conftest import NOW, F, MutableClock, build_f, fact_selection, headers, propose, rename

REQUEST = "el perro se llama Nala"


def _waiting_run(sf: sessionmaker[Session]) -> int:
    """Otra ejecución que ya espera en la cola, de otra novela."""
    other = build_f(sf)
    with unit_of_work(sf) as uow:
        run = models.Run(
            novel_id=other.novel_id,
            type="generation",
            status="queued",
            resumes=0,
            created_at=NOW,
        )
        uow.add(run)
        uow.session.flush()
        return run.id


def test_confirming_with_the_code_queues_a_change_run_on_v1_behind_the_waiting_one(
    client: TestClient,
    f: F,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    clock: MutableClock,
) -> None:
    waiting = _waiting_run(session_factory)
    propose(fake, rename(f.toby_name_fact, "Nala"))
    proposal = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": REQUEST},
        headers=headers(f.user_a),
    ).json()
    clock.advance(minutes=5)

    response = client.post(
        f"/api/change-requests/{proposal['id']}/confirm",
        json={"code": proposal["code"]},
        headers=headers(f.user_a),
    )

    assert response.status_code == 202, response.text
    run_id = response.json()["run_id"]
    with session_factory() as session:
        row = session.get_one(models.ChangeRequest, proposal["id"])
        assert (row.status, row.run_id) == ("confirmed", run_id)
        run = session.get_one(models.Run, run_id)
        assert (run.type, run.status, run.novel_id) == ("change_request", "queued", f.novel_id)
        assert (run.base_version_id, run.candidate_version_id) == (f.v1_id, None)
        assert [r.id for r in queued_runs(session)] == [waiting, run_id]
    novel = client.get(f"/api/novels/{f.novel_id}", headers=headers(f.user_a)).json()
    assert (novel["status"], novel["current_version"]) == ("published", 1)

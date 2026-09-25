"""014-C01 — Una petición sobre un hecho devuelve la propuesta, los afectados y el código."""

from __future__ import annotations

import datetime as dt

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import FakeAgent
from story_maker.store import models

from .conftest import F, MutableClock, fact_selection, headers, planner_message, propose, rename

REQUEST = "el perro se llama Nala"


def _ask(client: TestClient, f: F, fake: FakeAgent) -> dict[str, object]:
    propose(fake, rename(f.toby_name_fact, "Nala"))
    response = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": REQUEST},
        headers=headers(f.user_a),
    )
    assert response.status_code == 201, response.text
    return response.json()  # type: ignore[no-any-return]


def test_the_response_carries_the_proposal_with_the_old_value_from_v1_the_affected_and_a_code(
    client: TestClient, f: F, fake: FakeAgent
) -> None:
    body = _ask(client, f, fake)

    assert isinstance(body["id"], int)
    assert body["proposal"] == {
        "changes": [{"fact_id": f.toby_name_fact, "old_value": "Toby", "new_value": "Nala"}],
        "new_fact": None,
    }
    assert body["affected_chapters"] == [2, 5, 7]
    assert isinstance(body["code"], str)
    assert body["code"]


def test_the_request_stays_proposed_on_v1_expiring_after_the_confirmation_minutes(
    client: TestClient,
    f: F,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    clock: MutableClock,
) -> None:
    body = _ask(client, f, fake)

    with session_factory() as session:
        row = session.get_one(models.ChangeRequest, body["id"])
        assert row.status == "proposed"
        assert row.base_version_id == f.v1_id
        assert row.expires_at == clock.now + dt.timedelta(minutes=15)
        assert row.affected_chapters == [2, 5, 7]
        assert row.code_hash is not None
        assert row.code_hash != body["code"]
        assert body["code"] not in row.code_hash
        assert dt.datetime.fromisoformat(str(body["expires_at"])) == row.expires_at.replace(
            tzinfo=dt.UTC
        )


def test_one_planner_session_in_change_mode_without_run_received_selection_request_and_bible(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    _ask(client, f, fake)

    with session_factory() as session:
        rows = session.query(models.RoleSession).filter_by(novel_id=f.novel_id).all()
        assert [(r.role, r.run_id) for r in rows] == [("planner", None)]
    assert [(s.request.role, s.request.mode) for s in fake.sessions] == [("planner", "change")]
    message = planner_message(fake)
    assert message["selection"]["fact_id"] == f.toby_name_fact
    assert message["request"] == REQUEST
    assert "dato" in message["instructions"]
    bible_facts = {fact["id"]: fact["value"] for fact in message["story_bible"]["facts"]}
    assert bible_facts[f.toby_name_fact] == "Toby"
    assert message["story_bible"]["version_id"] == f.v1_id


def test_the_engine_decisions_on_the_request_and_the_new_value_are_allowed_with_origin_change(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    _ask(client, f, fake)

    with session_factory() as session:
        rows = (
            session.query(models.AuditLog)
            .filter_by(novel_id=f.novel_id, origin="change_request")
            .all()
        )
        assert [r.decision for r in rows] == ["allow", "allow"]


def test_nothing_is_queued_and_the_novel_stays_published_on_v1(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    _ask(client, f, fake)

    with session_factory() as session:
        assert session.query(models.Run).count() == 0
        versions = session.query(models.Version).filter_by(novel_id=f.novel_id).all()
        assert [(v.id, v.status, v.number) for v in versions] == [(f.v1_id, "published", 1)]
        toby = session.get_one(models.Fact, f.toby_name_fact)
        assert toby.value == "Toby"
    novel = client.get(f"/api/novels/{f.novel_id}", headers=headers(f.user_a)).json()
    assert novel["status"] == "published"
    assert novel["current_version"] == 1

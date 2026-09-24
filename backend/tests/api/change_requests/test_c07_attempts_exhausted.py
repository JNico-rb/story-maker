"""014-C07 — Agotados los intentos, la solicitud queda `rejected` (y 014-I6: como mucho
1 + `max_retries.change` intentos)."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, FakeAgent, Script
from story_maker.store import models

from .conftest import F, fact_selection, headers, rename

REQUEST = "el perro se llama Nala"


def _post(client: TestClient, f: F) -> Any:
    return client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": REQUEST},
        headers=headers(f.user_a),
    )


def _session(fake: FakeAgent, *proposals: dict[str, Any]) -> None:
    steps = tuple(Call("propose_change", proposal) for proposal in proposals)
    fake.script("planner", "change", Script(steps=steps))


def _v1_fingerprint(sf: sessionmaker[Session], f: F) -> tuple[Any, ...]:
    with sf() as session:
        chapters = session.query(models.Chapter).filter_by(version_id=f.v1_id)
        facts = session.query(models.Fact).filter_by(version_id=f.v1_id)
        return (
            sorted((c.number, c.content_hash) for c in chapters),
            sorted((x.id, x.value) for x in facts),
        )


def _assert_rejected_after_three_attempts(
    sf: sessionmaker[Session], f: F, fingerprint: tuple[Any, ...]
) -> None:
    with sf() as session:
        [row] = session.query(models.ChangeRequest).filter_by(novel_id=f.novel_id).all()
        assert (row.status, row.code_hash, row.run_id) == ("rejected", None, None)
        attempts = session.query(models.Attempt).filter_by(change_request_id=row.id)
        assert sorted((a.number, a.outcome) for a in attempts if a.evaluable == "change") == [
            (1, "rewrite"),
            (2, "rewrite"),
            (3, "fail"),
        ]
        assert session.query(models.Run).filter_by(novel_id=f.novel_id).count() == 0
    assert _v1_fingerprint(sf, f) == fingerprint


def test_three_invalid_proposals_leave_the_request_rejected_with_a_422_and_the_last_defects(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    unchanged = rename(f.toby_name_fact, "Toby")
    _session(fake, unchanged)
    _session(fake, unchanged)
    _session(fake, unchanged, rename(f.toby_name_fact, "Nala"))
    _session(fake, rename(f.toby_name_fact, "Nala"))
    fingerprint = _v1_fingerprint(session_factory, f)

    response = _post(client, f)

    assert response.status_code == 422, response.text
    assert response.json()["detail"] == {
        "defects": [f"El cambio no cambia nada: hecho {f.toby_name_fact}"]
    }
    assert len(fake.sessions) == 3
    _assert_rejected_after_three_attempts(session_factory, f, fingerprint)
    with session_factory() as session:
        planners = session.query(models.RoleSession).filter_by(novel_id=f.novel_id).all()
        assert [s.outcome for s in planners] == ["completed", "completed", "cut"]


def test_two_schema_errors_and_an_invalid_proposal_cut_the_session_at_the_third_attempt(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    _session(fake, {}, {})
    _session(fake, rename(f.toby_name_fact, "Toby"), rename(f.toby_name_fact, "Nala"))
    fingerprint = _v1_fingerprint(session_factory, f)

    response = _post(client, f)

    assert response.status_code == 422, response.text
    assert response.json()["detail"] == {
        "defects": [f"El cambio no cambia nada: hecho {f.toby_name_fact}"]
    }
    assert len(fake.sessions) == 2
    _assert_rejected_after_three_attempts(session_factory, f, fingerprint)
    with session_factory() as session:
        planners = session.query(models.RoleSession).filter_by(novel_id=f.novel_id).all()
        assert [s.outcome for s in planners] == ["completed", "cut"]

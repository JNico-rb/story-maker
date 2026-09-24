"""014-I1 — El código calcula los capítulos afectados desde la versión base; nada de la entrega
del planner los añade ni los quita (las fuentes de los afectados, en 014-C02)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, FakeAgent, Script
from story_maker.store import models

from .conftest import F, fact_selection, headers, rename

REQUEST = "el perro se llama Nala"


def test_a_delivery_that_names_its_own_affected_chapters_is_a_schema_error_and_v1_decides_them(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    own_affected = {**rename(f.toby_name_fact, "Nala"), "affected_chapters": [1, 9]}
    fake.script(
        "planner",
        "change",
        Script(
            steps=(
                Call("propose_change", own_affected),
                Call("propose_change", rename(f.toby_name_fact, "Nala")),
            )
        ),
    )

    response = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": REQUEST},
        headers=headers(f.user_a),
    )

    assert response.status_code == 201, response.text
    assert response.json()["affected_chapters"] == [2, 5, 7]
    with session_factory() as session:
        row = session.get_one(models.ChangeRequest, response.json()["id"])
        assert row.affected_chapters == [2, 5, 7]
        attempts = session.query(models.Attempt).filter_by(change_request_id=row.id)
        assert sorted((a.number, a.outcome) for a in attempts) == [(1, "rewrite"), (2, "accept")]
    [session_log] = fake.sessions
    assert "affected_chapters" in session_log.reads[0]  # el error de schema vuelve al planner

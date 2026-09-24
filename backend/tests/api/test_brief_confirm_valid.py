"""Confirmar un brief válido (008-C15)."""

from __future__ import annotations

import datetime as dt

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.store.models import ExtractedFact, FreeText, Interview

from .briefs import B0_CONTENT, seed_brief

NOW = dt.datetime(2026, 9, 24, 12, 0)


def _seed_two_facts(session_factory: sessionmaker[Session], novel_id: int) -> None:
    with session_factory() as session:
        free_text = FreeText(
            novel_id=novel_id, content="x", discarded_instructions=None, created_at=NOW
        )
        session.add(free_text)
        session.flush()
        session.add_all(
            [
                ExtractedFact(
                    free_text_id=free_text.id,
                    subject="Marta",
                    attribute="afecto",
                    value="quiere a Toby",
                    quote="quiere a Toby",
                    verified=True,
                    accepted=True,
                    mandatory=False,
                ),
                ExtractedFact(
                    free_text_id=free_text.id,
                    subject="Marta",
                    attribute="otro",
                    value="otro dato",
                    quote="otro dato",
                    verified=True,
                    accepted=None,
                    mandatory=False,
                ),
            ]
        )
        session.commit()


def test_confirming_b0_returns_the_confirmed_brief_and_its_personal_elements(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)
    _seed_two_facts(session_factory, novel_id)

    response = client.post(f"/api/novels/{novel_id}/brief/confirm", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "confirmed"
    assert body["missing_fields"] == []
    assert body["contradictions"] == []
    assert body["schema_errors"] == []

    elements = body["personal_elements"]
    assert len(elements) == 5
    by_field = {e["field"]: e for e in elements}
    assert by_field["recipient.name"]["mandatory"] is True
    assert by_field["recipient.name"]["origin"] == "brief_field"
    assert by_field["recipient.traits[0]"]["mandatory"] is False
    assert by_field["recollections[0]"]["mandatory"] is True
    assert by_field["close_ones[0]"]["mandatory"] is False
    accepted_fact_elements = [e for e in elements if e["origin"] == "extracted_fact"]
    assert len(accepted_fact_elements) == 1
    assert accepted_fact_elements[0]["mandatory"] is False

    ids = [e["id"] for e in elements]
    assert len(ids) == len(set(ids))


def test_the_novel_moves_to_ready_after_confirming(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)

    client.post(f"/api/novels/{novel_id}/brief/confirm", headers=auth_headers)

    detail = client.get(f"/api/novels/{novel_id}", headers=auth_headers).json()
    assert detail["status"] == "ready"


def test_confirming_does_not_open_any_role_session(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: object,
) -> None:
    from story_maker.agents.fake import FakeAgent

    assert isinstance(fake, FakeAgent)
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)

    client.post(f"/api/novels/{novel_id}/brief/confirm", headers=auth_headers)

    assert fake.sessions == []


def test_confirming_sends_a_schema_brief_score_of_1_to_the_interview_trace(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    telemetry: object,
) -> None:
    from story_maker.observability.null import NullObservability

    assert isinstance(telemetry, NullObservability)
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)

    client.post(f"/api/novels/{novel_id}/brief/confirm", headers=auth_headers)

    trace = telemetry.traces[f"interview:{novel_id}"]
    assert trace.name == "entrevista"
    scores = [s for s in trace.scores if s.name == "schema-brief"]
    assert [s.value for s in scores] == [1]


def test_confirming_leaves_the_interview_history_untouched(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)

    client.post(f"/api/novels/{novel_id}/brief/confirm", headers=auth_headers)

    with session_factory() as session:
        interview = session.query(Interview).filter(Interview.novel_id == novel_id).one()
        assert interview is not None

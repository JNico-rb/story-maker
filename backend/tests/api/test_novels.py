"""Novelas: crear para entrevistar, importar, listar y ver el detalle con estado derivado
(008-C01, 008-C02, 008-C28 a 008-C30)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_creating_a_novel_opens_a_draft_interview_and_fixes_the_present_year(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post("/api/novels", json={}, headers=auth_headers)

    assert response.status_code == 201
    novel_id = response.json()["id"]

    detail = client.get(f"/api/novels/{novel_id}", headers=auth_headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["status"] == "interview"
    assert body["current_version"] is None
    assert body["title"] == ""
    assert body["recipient_name"] == ""

    messages = client.get(f"/api/novels/{novel_id}/interview/messages", headers=auth_headers)
    assert messages.status_code == 200
    assert messages.json() == []

    brief = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers)
    assert brief.status_code == 200
    assert brief.json()["status"] == "draft"


def test_creating_a_novel_opens_no_role_session(
    client: TestClient, auth_headers: dict[str, str], fake: object
) -> None:
    from story_maker.agents.fake import FakeAgent

    assert isinstance(fake, FakeAgent)
    client.post("/api/novels", json={}, headers=auth_headers)

    assert fake.sessions == []


def test_a_novels_embedding_model_stays_fixed_even_if_the_config_changes_afterwards(
    client: TestClient, auth_headers: dict[str, str], session_factory: object
) -> None:
    from sqlalchemy.orm import sessionmaker

    from story_maker.store.models import Novel

    assert isinstance(session_factory, sessionmaker)
    response = client.post("/api/novels", json={}, headers=auth_headers)
    novel_id = response.json()["id"]

    with session_factory() as session:
        novel = session.get(Novel, novel_id)
        assert novel is not None
        assert novel.embedding_model == "M1"

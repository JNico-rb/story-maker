"""Mensaje rechazado antes de abrir la sesión (008-C08)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, FakeAgent, Say, Script

from .briefs import B0_CONTENT, seed_brief


def test_an_empty_or_whitespace_message_is_rejected_without_opening_a_session(
    client: TestClient, auth_headers: dict[str, str], fake: FakeAgent
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]

    for text in ("", "   "):
        response = client.post(
            f"/api/novels/{novel_id}/interview/messages",
            json={"text": text},
            headers=auth_headers,
        )
        assert response.status_code == 422

    assert fake.sessions == []


def test_a_4000_character_message_is_processed(
    client: TestClient, auth_headers: dict[str, str], fake: FakeAgent
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    fake.script("interviewer", None, Script(steps=(Say("Gracias."),)))

    response = client.post(
        f"/api/novels/{novel_id}/interview/messages",
        json={"text": "a" * 4000},
        headers=auth_headers,
    )

    assert response.status_code == 200


def test_a_4001_character_message_is_rejected_without_opening_a_session(
    client: TestClient, auth_headers: dict[str, str], fake: FakeAgent
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]

    response = client.post(
        f"/api/novels/{novel_id}/interview/messages",
        json={"text": "a" * 4001},
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert fake.sessions == []


def test_a_message_on_an_already_confirmed_brief_answers_409(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT, status="confirmed")
    fake.script(
        "interviewer", None, Script(steps=(Call("update_brief", {"tone": "epic"}), Say("Ok.")))
    )

    response = client.post(
        f"/api/novels/{novel_id}/interview/messages",
        json={"text": "cambia el tono"},
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert fake.sessions == []

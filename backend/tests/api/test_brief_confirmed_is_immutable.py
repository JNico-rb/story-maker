"""Un brief confirmado es inmutable (008-C17)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import FakeAgent

from .briefs import B0_CONTENT, seed_brief


def _confirmed_novel(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> int:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)
    response = client.post(f"/api/novels/{novel_id}/brief/confirm", headers=auth_headers)
    assert response.status_code == 200
    return novel_id


def test_a_message_answers_409_opens_no_session_and_leaves_the_brief_untouched(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = _confirmed_novel(client, auth_headers, session_factory)

    response = client.post(
        f"/api/novels/{novel_id}/interview/messages",
        json={"text": "un mensaje más"},
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert fake.sessions == []


def test_a_free_text_answers_409_and_opens_no_session(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = _confirmed_novel(client, auth_headers, session_factory)

    response = client.post(
        f"/api/novels/{novel_id}/free-texts",
        json={"content": "algo más sobre Marta"},
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert fake.sessions == []


def test_patching_a_fact_answers_409(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = _confirmed_novel(client, auth_headers, session_factory)

    response = client.patch(
        f"/api/novels/{novel_id}/brief/extracted-facts/1",
        json={"accepted": True},
        headers=auth_headers,
    )

    assert response.status_code == 409


def test_posting_and_deleting_a_novel_banned_term_answer_409(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = _confirmed_novel(client, auth_headers, session_factory)

    post_response = client.post(
        f"/api/novels/{novel_id}/banned-terms",
        json={"term": "algo", "type": "word"},
        headers=auth_headers,
    )
    delete_response = client.delete(f"/api/novels/{novel_id}/banned-terms/1", headers=auth_headers)

    assert post_response.status_code == 409
    assert delete_response.status_code == 409


def test_confirming_again_answers_409(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = _confirmed_novel(client, auth_headers, session_factory)

    response = client.post(f"/api/novels/{novel_id}/brief/confirm", headers=auth_headers)

    assert response.status_code == 409


def test_reads_still_answer_200_and_the_brief_stays_the_same(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = _confirmed_novel(client, auth_headers, session_factory)
    before = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()

    client.post(
        f"/api/novels/{novel_id}/interview/messages",
        json={"text": "un mensaje más"},
        headers=auth_headers,
    )

    brief_response = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers)
    messages_response = client.get(
        f"/api/novels/{novel_id}/interview/messages", headers=auth_headers
    )

    assert brief_response.status_code == 200
    assert messages_response.status_code == 200
    assert brief_response.json()["content"] == before["content"]


def test_the_user_level_list_stays_editable_without_reopening_the_brief(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = _confirmed_novel(client, auth_headers, session_factory)

    added = client.post(
        "/api/banned-terms", json={"term": "algo", "type": "word"}, headers=auth_headers
    )

    assert added.status_code == 201
    brief = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()
    assert brief["status"] == "confirmed"

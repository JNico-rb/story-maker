"""Lista prohibida de nivel `user` (008-C26)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from .briefs import B0_CONTENT, seed_brief


def test_posting_creates_a_user_level_entry(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/banned-terms", json={"term": "Pedro", "type": "word"}, headers=auth_headers
    )

    assert response.status_code == 201
    assert response.json()["level"] == "user"


def test_shape_and_duplicate_validation_matches_novel_level(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    topic_without_keywords = client.post(
        "/api/banned-terms", json={"term": "divorcio", "type": "topic"}, headers=auth_headers
    )
    empty_term = client.post(
        "/api/banned-terms", json={"term": "  ", "type": "word"}, headers=auth_headers
    )
    client.post("/api/banned-terms", json={"term": "Pedro", "type": "word"}, headers=auth_headers)
    duplicate = client.post(
        "/api/banned-terms", json={"term": "pedro", "type": "word"}, headers=auth_headers
    )

    assert topic_without_keywords.status_code == 422
    assert empty_term.status_code == 422
    assert duplicate.status_code == 409


def test_get_only_returns_the_clients_own_user_level_entries(
    client: TestClient,
    auth_headers: dict[str, str],
    other_client_headers: dict[str, str],
) -> None:
    client.post("/api/banned-terms", json={"term": "Pedro", "type": "word"}, headers=auth_headers)
    client.post(
        "/api/banned-terms", json={"term": "Ana", "type": "word"}, headers=other_client_headers
    )

    response = client.get("/api/banned-terms", headers=auth_headers)

    assert [row["term"] for row in response.json()] == ["Pedro"]


def test_deleting_another_clients_entry_answers_404(
    client: TestClient,
    auth_headers: dict[str, str],
    other_client_headers: dict[str, str],
) -> None:
    created = client.post(
        "/api/banned-terms", json={"term": "Ana", "type": "word"}, headers=other_client_headers
    ).json()

    response = client.delete(f"/api/banned-terms/{created['id']}", headers=auth_headers)

    assert response.status_code == 404


def test_it_works_regardless_of_the_clients_novels_state(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT, status="confirmed")

    response = client.post(
        "/api/banned-terms", json={"term": "Pedro", "type": "word"}, headers=auth_headers
    )

    assert response.status_code == 201


def test_a_new_entry_counts_in_c6_of_the_clients_drafts_on_the_next_read(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)
    before = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()
    assert not any(c["rule"] == "C6" for c in before["contradictions"])

    client.post("/api/banned-terms", json={"term": "camino", "type": "word"}, headers=auth_headers)

    after = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()
    assert any(c["rule"] == "C6" for c in after["contradictions"])


def test_a_new_entry_does_not_touch_the_novel_or_global_lists(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]

    client.post("/api/banned-terms", json={"term": "Pedro", "type": "word"}, headers=auth_headers)

    novel_terms = client.get(f"/api/novels/{novel_id}/banned-terms", headers=auth_headers).json()
    assert novel_terms == []

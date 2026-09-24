"""Lista prohibida de nivel `novel` (008-C25)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from .briefs import B0_CONTENT, seed_brief


def test_posting_a_word_creates_it_at_novel_level_with_its_normalized_form(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]

    response = client.post(
        f"/api/novels/{novel_id}/banned-terms",
        json={"term": "Pedro", "type": "word"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["level"] == "novel"
    assert body["normalized"] == "pedro"


def test_posting_a_topic_with_keywords_succeeds(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]

    response = client.post(
        f"/api/novels/{novel_id}/banned-terms",
        json={"term": "divorcio", "type": "topic", "keywords": ["divorcio", "separación"]},
        headers=auth_headers,
    )

    assert response.status_code == 201


def test_a_topic_without_keywords_or_a_word_with_keywords_is_rejected(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]

    topic_without_keywords = client.post(
        f"/api/novels/{novel_id}/banned-terms",
        json={"term": "divorcio", "type": "topic"},
        headers=auth_headers,
    )
    word_with_keywords = client.post(
        f"/api/novels/{novel_id}/banned-terms",
        json={"term": "pedro", "type": "word", "keywords": ["algo"]},
        headers=auth_headers,
    )

    assert topic_without_keywords.status_code == 422
    assert word_with_keywords.status_code == 422


def test_an_empty_term_is_rejected(client: TestClient, auth_headers: dict[str, str]) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]

    response = client.post(
        f"/api/novels/{novel_id}/banned-terms",
        json={"term": "  ", "type": "word"},
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_the_same_normalized_form_and_type_is_a_conflict(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    client.post(
        f"/api/novels/{novel_id}/banned-terms",
        json={"term": "Pedro", "type": "word"},
        headers=auth_headers,
    )

    response = client.post(
        f"/api/novels/{novel_id}/banned-terms",
        json={"term": "pedro", "type": "word"},
        headers=auth_headers,
    )

    assert response.status_code == 409


def test_get_only_returns_this_novels_entries(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    other_novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    client.post(
        f"/api/novels/{novel_id}/banned-terms",
        json={"term": "Pedro", "type": "word"},
        headers=auth_headers,
    )
    client.post(
        f"/api/novels/{other_novel_id}/banned-terms",
        json={"term": "Ana", "type": "word"},
        headers=auth_headers,
    )
    client.post("/api/banned-terms", json={"term": "algo", "type": "word"}, headers=auth_headers)

    response = client.get(f"/api/novels/{novel_id}/banned-terms", headers=auth_headers)

    assert response.status_code == 200
    terms = [row["term"] for row in response.json()]
    assert terms == ["Pedro"]


def test_deleting_an_entry_works_even_if_the_interviewer_registered_it(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    created = client.post(
        f"/api/novels/{novel_id}/banned-terms",
        json={"term": "Pedro", "type": "word"},
        headers=auth_headers,
    ).json()

    response = client.delete(
        f"/api/novels/{novel_id}/banned-terms/{created['id']}", headers=auth_headers
    )

    assert response.status_code == 204
    remaining = client.get(f"/api/novels/{novel_id}/banned-terms", headers=auth_headers).json()
    assert remaining == []


def test_deleting_a_missing_or_foreign_novels_entry_is_404(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    other_novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    created = client.post(
        f"/api/novels/{other_novel_id}/banned-terms",
        json={"term": "Ana", "type": "word"},
        headers=auth_headers,
    ).json()

    missing = client.delete(f"/api/novels/{novel_id}/banned-terms/999999", headers=auth_headers)
    foreign = client.delete(
        f"/api/novels/{novel_id}/banned-terms/{created['id']}", headers=auth_headers
    )

    assert missing.status_code == 404
    assert foreign.status_code == 404


def test_post_and_delete_are_rejected_once_the_brief_is_confirmed_but_get_still_works(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    created = client.post(
        f"/api/novels/{novel_id}/banned-terms",
        json={"term": "Pedro", "type": "word"},
        headers=auth_headers,
    ).json()
    seed_brief(session_factory, novel_id, B0_CONTENT, status="confirmed")

    post_after_confirm = client.post(
        f"/api/novels/{novel_id}/banned-terms",
        json={"term": "Ana", "type": "word"},
        headers=auth_headers,
    )
    delete_after_confirm = client.delete(
        f"/api/novels/{novel_id}/banned-terms/{created['id']}", headers=auth_headers
    )
    get_after_confirm = client.get(f"/api/novels/{novel_id}/banned-terms", headers=auth_headers)

    assert post_after_confirm.status_code == 409
    assert delete_after_confirm.status_code == 409
    assert get_after_confirm.status_code == 200

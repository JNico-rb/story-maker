"""Texto libre rechazado o con la sesión fallida (008-C23)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, Fail, FakeAgent, Script

from .briefs import B0_CONTENT, seed_brief


def test_an_empty_or_whitespace_text_is_rejected_without_a_session(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)

    for content in ("", "   "):
        response = client.post(
            f"/api/novels/{novel_id}/free-texts", json={"content": content}, headers=auth_headers
        )
        assert response.status_code == 422

    assert fake.sessions == []


def test_a_20000_character_text_is_processed(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)
    fake.script("extractor", None, Script(steps=(Call("submit_facts", {"facts": []}),)))

    response = client.post(
        f"/api/novels/{novel_id}/free-texts", json={"content": "a" * 20000}, headers=auth_headers
    )

    assert response.status_code == 201


def test_a_20001_character_text_is_rejected_without_a_session(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)

    response = client.post(
        f"/api/novels/{novel_id}/free-texts", json={"content": "a" * 20001}, headers=auth_headers
    )

    assert response.status_code == 422
    assert fake.sessions == []


def test_a_brief_with_no_valid_subject_yet_answers_409(
    client: TestClient, auth_headers: dict[str, str], fake: FakeAgent
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]

    response = client.post(
        f"/api/novels/{novel_id}/free-texts", json={"content": "algo"}, headers=auth_headers
    )

    assert response.status_code == 409
    assert fake.sessions == []


def test_a_confirmed_brief_answers_409(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT, status="confirmed")

    response = client.post(
        f"/api/novels/{novel_id}/free-texts", json={"content": "algo"}, headers=auth_headers
    )

    assert response.status_code == 409
    assert fake.sessions == []


def test_a_provider_failure_answers_503(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)
    fake.script("extractor", None, Script(steps=(Fail(),)))

    response = client.post(
        f"/api/novels/{novel_id}/free-texts", json={"content": "algo"}, headers=auth_headers
    )

    assert response.status_code == 503


def test_the_extractor_ending_without_delivering_submit_facts_answers_503(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    from story_maker.agents.fake import Say

    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)
    fake.script("extractor", None, Script(steps=(Say("No he encontrado nada."),)))

    response = client.post(
        f"/api/novels/{novel_id}/free-texts", json={"content": "algo"}, headers=auth_headers
    )

    assert response.status_code == 503


def test_the_extractor_delivering_twice_processes_only_the_last_one(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)
    first = {"facts": [{"subject": "Marta", "attribute": "a", "value": "primero", "quote": "algo"}]}
    second = {"facts": [{"subject": "Toby", "attribute": "b", "value": "segundo", "quote": "algo"}]}
    fake.script(
        "extractor",
        None,
        Script(steps=(Call("submit_facts", first), Call("submit_facts", second))),
    )

    response = client.post(
        f"/api/novels/{novel_id}/free-texts", json={"content": "algo"}, headers=auth_headers
    )

    assert response.status_code == 201
    assert len(response.json()["verified_facts"]) == 1
    assert response.json()["verified_facts"][0]["subject"] == "Toby"

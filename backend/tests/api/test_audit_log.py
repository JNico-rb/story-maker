"""Audit log de la novela (008-C27)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, FakeAgent, Say, Script
from story_maker.store.models import BannedTerm

from .briefs import B0_CONTENT, seed_brief


def test_returns_the_novels_decisions_in_chronological_order(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, {**B0_CONTENT, "dedication": ""})
    with session_factory() as session:
        session.add(
            BannedTerm(
                level="novel",
                user_id=None,
                novel_id=novel_id,
                term="pedro",
                type="word",
                keywords=None,
                normalized="pedro",
            )
        )
        session.commit()
    fake.script(
        "interviewer",
        None,
        Script(
            steps=(
                Call("update_brief", {"tone": "epic", "dedication": "Para Marta, de Pedro"}),
                Say("Vale."),
            )
        ),
    )
    client.post(
        f"/api/novels/{novel_id}/interview/messages",
        json={"text": "prueba"},
        headers=auth_headers,
    )
    fake.script("extractor", None, Script(steps=(Call("submit_facts", {"facts": []}),)))
    client.post(
        f"/api/novels/{novel_id}/free-texts",
        json={"content": "un texto cualquiera"},
        headers=auth_headers,
    )

    response = client.get(f"/api/novels/{novel_id}/audit-log", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert [row["origin"] for row in body] == ["policy_hook", "free_text", "policy_hook"]
    assert body[0]["decision"] == "deny"
    times = [row["created_at"] for row in body]
    assert times == sorted(times)


def test_does_not_show_decisions_from_other_novels(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    other_novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, other_novel_id, {**B0_CONTENT, "dedication": ""})
    with session_factory() as session:
        session.add(
            BannedTerm(
                level="novel",
                user_id=None,
                novel_id=other_novel_id,
                term="pedro",
                type="word",
                keywords=None,
                normalized="pedro",
            )
        )
        session.commit()
    fake.script(
        "interviewer",
        None,
        Script(
            steps=(
                Call("update_brief", {"dedication": "Para Marta, de Pedro"}),
                Say("Vale."),
            )
        ),
    )
    client.post(
        f"/api/novels/{other_novel_id}/interview/messages",
        json={"text": "prueba"},
        headers=auth_headers,
    )

    response = client.get(f"/api/novels/{novel_id}/audit-log", headers=auth_headers)

    assert response.json() == []


def test_a_novel_with_no_decisions_has_an_empty_log(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]

    response = client.get(f"/api/novels/{novel_id}/audit-log", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []

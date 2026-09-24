"""Una dedicatoria con una prohibida no entra por `update_brief` (008-C06)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, FakeAgent, Say, Script
from story_maker.store.models import AuditLog, BannedTerm

from .briefs import B0_CONTENT, seed_brief


def _novel_with_pedro_banned(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> int:
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
    return novel_id


def test_the_policy_hook_denies_the_whole_delivery_and_the_dedication_keeps_missing(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = _novel_with_pedro_banned(client, auth_headers, session_factory)
    fake.script(
        "interviewer",
        None,
        Script(
            steps=(
                Call("update_brief", {"tone": "epic", "dedication": "Para Marta, lejos de Pedro"}),
                Say("Vale, lo dejamos así."),
            )
        ),
    )

    response = client.post(
        f"/api/novels/{novel_id}/interview/messages",
        json={"text": "Que la dedicatoria hable de Pedro"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()
    assert body["content"]["tone"] == B0_CONTENT["tone"]  # nada de la entrega se aplica
    assert body["content"]["dedication"] == ""
    assert "dedication" in body["missing_fields"]

    messages = client.get(f"/api/novels/{novel_id}/interview/messages", headers=auth_headers).json()
    assert [m["author"] for m in messages] == ["user", "interviewer"]

    with session_factory() as session:
        rows = session.query(AuditLog).filter(AuditLog.novel_id == novel_id).all()
        assert len(rows) == 1
        assert rows[0].decision == "deny"
        assert rows[0].origin == "policy_hook"


def test_the_hook_does_not_scan_the_banned_entries_field_or_a_close_ones_name(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = _novel_with_pedro_banned(client, auth_headers, session_factory)
    close_ones = [{"name": "Pedro", "relation": "amigo", "species": "person", "mandatory": False}]
    fake.script(
        "interviewer",
        None,
        Script(
            steps=(
                Call(
                    "update_brief",
                    {
                        "banned_entries": [{"term": "pedro", "type": "word"}],
                        "close_ones": close_ones,
                    },
                ),
                Say("Anotado."),
            )
        ),
    )

    response = client.post(
        f"/api/novels/{novel_id}/interview/messages",
        json={"text": "Pedro es su amigo, y prohíbe hablar de Pedro"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()
    assert [c["name"] for c in body["content"]["close_ones"]] == ["Pedro"]

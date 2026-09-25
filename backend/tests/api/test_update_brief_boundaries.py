"""`update_brief` no alcanza lo que decide el cliente (008-C05)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, FakeAgent, Say, Script
from story_maker.store.models import BannedTerm

from .briefs import B0_CONTENT, seed_brief

_FORBIDDEN_DELIVERIES = (
    {"status": "confirmed"},
    {"extracted_facts": [{"id": 1, "accepted": True}]},
    {"extracted_facts": [{"id": 1, "mandatory": True}]},
    {"remove_banned_entries": ["pedro"]},
    {"user_banned_entries": [{"term": "algo", "type": "word"}]},
    {"global_banned_entries": [{"term": "algo", "type": "word"}]},
    {"genre": "ciencia ficción"},
    {"banned_entries": [{"term": "divorcio", "type": "topic"}]},
    {"banned_entries": [{"term": "pedro", "type": "word", "keywords": ["pedro"]}]},
    {"banned_entries": [{"term": "  ", "type": "word"}]},
)


def test_none_of_those_deliveries_change_anything(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)

    fake.script(
        "interviewer",
        None,
        Script(
            steps=(
                *(Call("update_brief", patch) for patch in _FORBIDDEN_DELIVERIES),
                Say("No he podido aplicar eso."),
            )
        ),
    )

    response = client.post(
        f"/api/novels/{novel_id}/interview/messages",
        json={"text": "intenta algo raro"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()
    assert body["status"] == "draft"
    assert body["content"] == B0_CONTENT

    with session_factory() as session:
        assert session.query(BannedTerm).filter(BannedTerm.novel_id == novel_id).count() == 0

    update_brief_calls = [c for c in fake.sessions[0].hooks.calls if c.tool == "update_brief"]
    assert len(update_brief_calls) == len(_FORBIDDEN_DELIVERIES)
    assert all(call.status == "schema_rejected" for call in update_brief_calls)

"""`update_brief` actúa como parche del borrador (008-C04)."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, FakeAgent, Say, Script
from story_maker.store.models import BannedTerm

from .briefs import B0_CONTENT, seed_brief


def _new_novel(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> int:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)
    return novel_id


def _deliver(
    client: TestClient,
    fake: FakeAgent,
    novel_id: int,
    auth_headers: dict[str, str],
    *patches: dict[str, Any],
) -> dict[str, Any]:
    fake.script(
        "interviewer",
        None,
        Script(steps=(*(Call("update_brief", p) for p in patches), Say("Entendido."))),
    )
    response = client.post(
        f"/api/novels/{novel_id}/interview/messages",
        json={"text": "un turno cualquiera"},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.json()
    return client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()  # type: ignore[no-any-return]


def test_only_the_tone_changes(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = _new_novel(client, auth_headers, session_factory)

    body = _deliver(client, fake, novel_id, auth_headers, {"tone": "funny"})

    assert body["content"]["tone"] == "funny"
    assert body["content"]["genre"] == B0_CONTENT["genre"]
    assert body["content"]["recipient"]["name"] == "Marta"


def test_an_empty_birth_date_clears_it_and_the_age_stays(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = _new_novel(client, auth_headers, session_factory)

    body = _deliver(client, fake, novel_id, auth_headers, {"birth_date": None})

    assert body["content"]["recipient"]["birth_date"] is None
    assert body["content"]["recipient"]["age"] == 40


def test_the_close_ones_list_becomes_exactly_what_was_delivered(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = _new_novel(client, auth_headers, session_factory)
    close_ones = [
        {
            "name": "Toby",
            "relation": "mascota",
            "species": "animal",
            "age": None,
            "birth_date": None,
            "mandatory": False,
        },
        {
            "name": "Luis",
            "relation": "amigo",
            "species": "person",
            "age": 41,
            "birth_date": None,
            "mandatory": False,
        },
    ]

    body = _deliver(client, fake, novel_id, auth_headers, {"close_ones": close_ones})

    assert [c["name"] for c in body["content"]["close_ones"]] == ["Toby", "Luis"]


def test_an_empty_traits_list_leaves_no_trait_at_all(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = _new_novel(client, auth_headers, session_factory)

    body = _deliver(client, fake, novel_id, auth_headers, {"traits": []})

    assert body["content"]["recipient"]["traits"] == []
    assert "traits" in body["missing_fields"]


def test_a_new_novel_banned_word_is_added_with_its_normalized_form(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = _new_novel(client, auth_headers, session_factory)

    _deliver(
        client,
        fake,
        novel_id,
        auth_headers,
        {"banned_entries": [{"term": "Pedro", "type": "word"}]},
    )

    with session_factory() as session:
        rows = session.query(BannedTerm).filter(BannedTerm.novel_id == novel_id).all()
        assert [(r.term, r.level, r.normalized) for r in rows] == [("Pedro", "novel", "pedro")]


def test_the_same_word_again_is_not_added_twice(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = _new_novel(client, auth_headers, session_factory)
    _deliver(
        client,
        fake,
        novel_id,
        auth_headers,
        {"banned_entries": [{"term": "Pedro", "type": "word"}]},
    )

    _deliver(
        client,
        fake,
        novel_id,
        auth_headers,
        {"banned_entries": [{"term": "pedro", "type": "word"}]},
    )

    with session_factory() as session:
        rows = session.query(BannedTerm).filter(BannedTerm.novel_id == novel_id).all()
        assert len(rows) == 1


def test_banned_asked_gets_marked(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, {**B0_CONTENT, "banned_asked": False})

    body = _deliver(client, fake, novel_id, auth_headers, {"banned_asked": True})

    assert body["content"]["banned_asked"] is True
    assert "banned_asked" not in body["missing_fields"]


def test_several_deliveries_in_one_turn_apply_in_order(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = _new_novel(client, auth_headers, session_factory)

    body = _deliver(client, fake, novel_id, auth_headers, {"tone": "funny"}, {"tone": "epic"})

    assert body["content"]["tone"] == "epic"

"""Un turno de la entrevista aplica lo que entrega `update_brief` (008-C03)."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from story_maker.agents.fake import Call, FakeAgent, Say, Script


def _script_delivering_name_and_age(fake: FakeAgent) -> None:
    fake.script(
        "interviewer",
        None,
        Script(
            steps=(
                Call("update_brief", {"name": "Marta", "age": 40}),
                Say("¿Cómo es Marta?"),
            )
        ),
    )


def test_a_turn_applies_what_the_interviewer_delivers(
    client: TestClient, auth_headers: dict[str, str], fake: FakeAgent
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    _script_delivering_name_and_age(fake)

    response = client.post(
        f"/api/novels/{novel_id}/interview/messages",
        json={"text": "Se llama Marta y cumple 40"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "¿Cómo es Marta?"
    assert "name" not in body["brief"]["missing_fields"]
    assert "age" not in body["brief"]["missing_fields"]

    messages = client.get(f"/api/novels/{novel_id}/interview/messages", headers=auth_headers).json()
    assert [(m["author"], m["text"]) for m in messages] == [
        ("user", "Se llama Marta y cumple 40"),
        ("interviewer", "¿Cómo es Marta?"),
    ]


def test_the_session_receives_the_history_the_brief_the_facts_and_the_checks(
    client: TestClient, auth_headers: dict[str, str], fake: FakeAgent
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    _script_delivering_name_and_age(fake)

    client.post(
        f"/api/novels/{novel_id}/interview/messages",
        json={"text": "Se llama Marta y cumple 40"},
        headers=auth_headers,
    )

    sent = json.loads(fake.sessions[0].request.message)
    assert sent["history"] == []
    assert sent["brief"]["recipient"]["name"] == ""
    assert sent["novel_banned_terms"] == []
    assert sent["verified_facts"] == []
    assert "name" in sent["checks"]["missing_fields"]
    assert "age" in sent["checks"]["missing_fields"]
    assert sent["message"] == "Se llama Marta y cumple 40"

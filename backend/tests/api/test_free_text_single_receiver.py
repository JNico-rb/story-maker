"""El texto libre solo llega al extractor (008-C22)."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, FakeAgent, Say, Script

from .briefs import B0_CONTENT, seed_brief

WITNESS_PHRASE = "el zafiro escondido bajo la tercera baldosa"
LETTER = f"Querida Marta: {WITNESS_PHRASE}. Un abrazo."


def test_the_witness_phrase_only_reaches_the_extractors_session(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)

    fake.script(
        "extractor",
        None,
        Script(
            steps=(
                Call(
                    "submit_facts",
                    {
                        "facts": [
                            {
                                "subject": "Marta",
                                "attribute": "secreto",
                                "value": "un zafiro escondido",
                                "quote": WITNESS_PHRASE,
                            }
                        ]
                    },
                ),
            )
        ),
    )
    extraction = client.post(
        f"/api/novels/{novel_id}/free-texts",
        json={"content": LETTER},
        headers=auth_headers,
    )
    assert extraction.status_code == 201

    fake.script(
        "interviewer", None, Script(steps=(Call("update_brief", {"tone": "funny"}), Say("Ok.")))
    )
    fake.script(
        "interviewer", None, Script(steps=(Call("update_brief", {"tone": "epic"}), Say("Ok.")))
    )
    client.post(
        f"/api/novels/{novel_id}/interview/messages",
        json={"text": "primer turno"},
        headers=auth_headers,
    )
    client.post(
        f"/api/novels/{novel_id}/interview/messages",
        json={"text": "segundo turno"},
        headers=auth_headers,
    )

    extractor_session = fake.sessions[0]
    interviewer_sessions = fake.sessions[1:]

    extractor_message = extractor_session.request.message
    assert extractor_message.count(WITNESS_PHRASE) == 1
    extractor_payload = json.loads(extractor_message)
    assert WITNESS_PHRASE in extractor_payload["data"]

    for session in interviewer_sessions:
        assert WITNESS_PHRASE not in session.request.message


def test_the_interviewer_sees_facts_without_their_quote(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)
    fake.script(
        "extractor",
        None,
        Script(
            steps=(
                Call(
                    "submit_facts",
                    {
                        "facts": [
                            {
                                "subject": "Marta",
                                "attribute": "secreto",
                                "value": "un zafiro escondido",
                                "quote": WITNESS_PHRASE,
                            }
                        ]
                    },
                ),
            )
        ),
    )
    client.post(
        f"/api/novels/{novel_id}/free-texts", json={"content": LETTER}, headers=auth_headers
    )

    fake.script(
        "interviewer", None, Script(steps=(Call("update_brief", {"tone": "funny"}), Say("Ok.")))
    )
    client.post(
        f"/api/novels/{novel_id}/interview/messages",
        json={"text": "un turno"},
        headers=auth_headers,
    )

    interviewer_payload = json.loads(fake.sessions[1].request.message)
    facts = interviewer_payload["verified_facts"]
    assert len(facts) == 1
    assert set(facts[0].keys()) == {"subject", "attribute", "value", "accepted", "mandatory"}


def test_the_client_sees_the_quote_in_the_free_text_response_and_in_get_brief(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)
    fake.script(
        "extractor",
        None,
        Script(
            steps=(
                Call(
                    "submit_facts",
                    {
                        "facts": [
                            {
                                "subject": "Marta",
                                "attribute": "secreto",
                                "value": "un zafiro escondido",
                                "quote": WITNESS_PHRASE,
                            }
                        ]
                    },
                ),
            )
        ),
    )
    extraction = client.post(
        f"/api/novels/{novel_id}/free-texts", json={"content": LETTER}, headers=auth_headers
    ).json()
    assert extraction["verified_facts"][0]["quote"] == WITNESS_PHRASE

    brief = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()
    assert brief["verified_facts"][0]["quote"] == WITNESS_PHRASE

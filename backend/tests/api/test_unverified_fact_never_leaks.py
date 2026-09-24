"""Un hecho sin verificar no sale nunca (008-I3): barrido de respuestas y entradas capturadas
con los fixtures de 008-C18 a 008-C21 y 008-C28."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, FakeAgent, Say, Script
from story_maker.store.models import ExtractedFact

from .briefs import B0_CONTENT, seed_brief
from .test_free_text_exfiltration import FAKE_CLAUDE_MD
from .test_free_text_exfiltration import LETTER as EXFILTRATION_LETTER
from .test_free_text_extraction import FACTS as EXTRACTION_FACTS
from .test_free_text_extraction import LETTER as EXTRACTION_LETTER
from .test_free_text_injection import FACTS as INJECTION_FACTS
from .test_free_text_injection import LETTER as INJECTION_LETTER
from .test_novel_import_valid import _import_body

# Los valores de los hechos que el código debe descartar en cada guion (008-C18, C20, C21).
_UNVERIFIED_VALUES = ["la playa", "Marta es valiente", "odea el mar", FAKE_CLAUDE_MD]


def _post_letter(
    client: TestClient,
    auth_headers: dict[str, str],
    novel_id: int,
    fake: FakeAgent,
    facts: list[dict[str, object]],
    letter: str,
) -> dict[str, object]:
    fake.script(
        "extractor",
        None,
        Script(steps=(Call("submit_facts", {"facts": facts, "discarded_instructions": []}),)),
    )
    response = client.post(
        f"/api/novels/{novel_id}/free-texts", json={"content": letter}, headers=auth_headers
    )
    assert response.status_code == 201, response.json()
    return response.json()  # type: ignore[no-any-return]


def _assert_no_unverified_value(payload: object) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    for value in _UNVERIFIED_VALUES:
        assert value not in text, f"{value!r} filtró en {text!r}"


def test_c18_extraction_never_leaks_the_two_unverified_facts(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)

    body = _post_letter(client, auth_headers, novel_id, fake, EXTRACTION_FACTS, EXTRACTION_LETTER)
    _assert_no_unverified_value(body)

    brief = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()
    _assert_no_unverified_value(brief["verified_facts"])


def test_c20_injection_never_leaks_the_sea_fact(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)

    body = _post_letter(client, auth_headers, novel_id, fake, INJECTION_FACTS, INJECTION_LETTER)
    _assert_no_unverified_value(body)

    brief = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()
    _assert_no_unverified_value(brief["verified_facts"])


def test_c21_the_exfiltrated_claude_md_never_leaks(
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
                                "attribute": "instrucciones",
                                "value": FAKE_CLAUDE_MD,
                                "quote": FAKE_CLAUDE_MD,
                            }
                        ]
                    },
                ),
            )
        ),
    )

    response = client.post(
        f"/api/novels/{novel_id}/free-texts",
        json={"content": EXFILTRATION_LETTER},
        headers=auth_headers,
    )
    assert response.status_code == 201
    _assert_no_unverified_value(response.json())

    brief = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()
    _assert_no_unverified_value(brief["verified_facts"])


def test_none_of_the_unverified_facts_ever_reach_the_interviewers_message(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)
    _post_letter(client, auth_headers, novel_id, fake, EXTRACTION_FACTS, EXTRACTION_LETTER)
    _post_letter(client, auth_headers, novel_id, fake, INJECTION_FACTS, INJECTION_LETTER)

    fake.script("interviewer", None, Script(steps=(Say("Vale."),)))
    client.post(
        f"/api/novels/{novel_id}/interview/messages",
        json={"text": "sigamos"},
        headers=auth_headers,
    )

    interviewer_session = next(s for s in fake.sessions if s.request.role == "interviewer")
    _assert_no_unverified_value(interviewer_session.request.message)


def test_c28_import_never_accepts_an_unverified_fact(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    fake.script(
        "extractor",
        None,
        Script(
            steps=(Call("submit_facts", {"facts": EXTRACTION_FACTS, "discarded_instructions": []}),)
        ),
    )
    response = client.post("/api/novels", json=_import_body(), headers=auth_headers)
    novel_id = response.json()["id"]

    body = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()
    _assert_no_unverified_value(body)

    with session_factory() as session:
        facts = session.query(ExtractedFact).all()
        for fact in facts:
            if not fact.verified:
                assert fact.accepted is not True

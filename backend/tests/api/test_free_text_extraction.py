"""Extraer hechos de un texto libre (008-C18)."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, FakeAgent, Script
from story_maker.store.models import AuditLog, ExtractedFact, FreeText

from .briefs import B0_CONTENT, seed_brief

LETTER = (
    "Querida Marta: aún me acuerdo de cuando Toby se comió tu bocadillo en la playa. "
    "Luis dice que eres la más valiente."
)

FACTS = [
    {
        "subject": "Toby",
        "attribute": "travesura",
        "value": "se comió el bocadillo de Marta",
        "quote": "Toby se comió tu bocadillo",
    },
    {
        "subject": "Marta",
        "attribute": "lugar favorito",
        "value": "la playa",
        "quote": "tu playa favorita",
    },
    {
        "subject": "Luis",
        "attribute": "opinión",
        "value": "Marta es valiente",
        "quote": "Luis dice que eres la más valiente",
    },
]


def _post_letter(
    client: TestClient, auth_headers: dict[str, str], novel_id: int, fake: FakeAgent
) -> dict[str, object]:
    fake.script(
        "extractor",
        None,
        Script(steps=(Call("submit_facts", {"facts": FACTS, "discarded_instructions": []}),)),
    )
    response = client.post(
        f"/api/novels/{novel_id}/free-texts",
        json={"content": LETTER},
        headers=auth_headers,
    )
    assert response.status_code == 201, response.json()
    return response.json()  # type: ignore[no-any-return]


def test_only_tobys_fact_comes_back_verified_unaccepted_and_not_mandatory(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)

    body = _post_letter(client, auth_headers, novel_id, fake)

    assert len(body["verified_facts"]) == 1
    fact = body["verified_facts"][0]
    assert fact["subject"] == "Toby"
    assert fact["accepted"] is None
    assert fact["mandatory"] is False


def test_the_free_text_and_all_three_facts_are_saved_marked_verified_or_not(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)

    _post_letter(client, auth_headers, novel_id, fake)

    with session_factory() as session:
        free_texts = session.query(FreeText).filter(FreeText.novel_id == novel_id).all()
        assert len(free_texts) == 1
        assert free_texts[0].content == LETTER
        facts = (
            session.query(ExtractedFact)
            .filter(ExtractedFact.free_text_id == free_texts[0].id)
            .order_by(ExtractedFact.id)
            .all()
        )
        assert [f.verified for f in facts] == [True, False, False]


def test_citas_verificadas_scores_0_with_two_discarded(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
    telemetry: object,
) -> None:
    from story_maker.observability.null import NullObservability

    assert isinstance(telemetry, NullObservability)
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)

    _post_letter(client, auth_headers, novel_id, fake)

    trace = telemetry.traces[f"interview:{novel_id}"]
    scores = [s for s in trace.scores if s.name == "citas-verificadas"]
    assert [s.value for s in scores] == [0]
    assert scores[0].comment is not None
    assert "2" in scores[0].comment


def test_the_audit_log_has_an_allow_decision_with_origin_free_text(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)

    _post_letter(client, auth_headers, novel_id, fake)

    with session_factory() as session:
        # También hay una decisión policy_hook (allow) por la propia llamada a submit_facts:
        # aquí solo importa la del texto libre en sí (origen free_text).
        rows = (
            session.query(AuditLog)
            .filter(AuditLog.novel_id == novel_id, AuditLog.origin == "free_text")
            .all()
        )
        assert len(rows) == 1
        assert rows[0].decision == "allow"


def test_the_extractor_receives_the_text_as_data_and_only_martas_and_tobys_subjects(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)

    _post_letter(client, auth_headers, novel_id, fake)

    sent = json.loads(fake.sessions[0].request.message)
    assert sent["data"] == LETTER
    names = {s["name"] for s in sent["valid_subjects"]}
    assert names == {"Marta", "Toby"}

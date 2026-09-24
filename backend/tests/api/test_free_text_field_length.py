"""`citas-verificadas`: un campo de más de 500 caracteres no llega a juzgarse (008-C19)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, FakeAgent, Script

from .briefs import B0_CONTENT, seed_brief


def test_an_oversized_field_bounces_back_as_a_schema_error_not_a_verification(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)
    oversized_fact = {
        "subject": "Marta",
        "attribute": "algo",
        "value": "x" * 501,
        "quote": "x" * 501,
    }
    fake.script(
        "extractor",
        None,
        Script(steps=(Call("submit_facts", {"facts": [oversized_fact]}),)),
    )

    response = client.post(
        f"/api/novels/{novel_id}/free-texts",
        json={"content": "un texto cualquiera"},
        headers=auth_headers,
    )

    assert response.status_code == 503
    call = fake.sessions[0].hooks.calls[0]
    assert call.status == "schema_rejected"

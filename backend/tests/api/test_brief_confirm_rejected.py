"""Confirmación rechazada (008-C16)."""

from __future__ import annotations

import copy

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from .briefs import B0_CONTENT, seed_brief


def _confirm(client: TestClient, auth_headers: dict[str, str], novel_id: int) -> dict[str, object]:
    response = client.post(f"/api/novels/{novel_id}/brief/confirm", headers=auth_headers)
    assert response.status_code == 422
    return response.json()  # type: ignore[no-any-return]


def test_missing_dedication_is_rejected_and_the_brief_stays_a_draft(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    content = copy.deepcopy(B0_CONTENT)
    content["dedication"] = ""
    seed_brief(session_factory, novel_id, content)

    body = _confirm(client, auth_headers, novel_id)

    assert any(item["type"] == "missing_field" for item in body["detail"])
    brief = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()
    assert brief["status"] == "draft"


def test_age_eleven_and_romance_is_rejected_with_the_contradiction(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    content = copy.deepcopy(B0_CONTENT)
    content["recipient"]["age"] = 11
    content["genre"] = "romance"
    seed_brief(session_factory, novel_id, content)

    body = _confirm(client, auth_headers, novel_id)

    assert any(item["type"] == "contradiction" for item in body["detail"])


def test_nine_mandatory_elements_is_rejected_with_the_cap(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    content = copy.deepcopy(B0_CONTENT)
    content["close_ones"] = [
        {
            "name": f"Amigo{i}",
            "relation": "amigo",
            "species": "person",
            "age": None,
            "birth_date": None,
            "mandatory": True,
        }
        for i in range(7)
    ]
    seed_brief(session_factory, novel_id, content)

    body = _confirm(client, auth_headers, novel_id)

    assert any(item["type"] == "mandatory_cap" for item in body["detail"])


def test_an_unknown_present_is_rejected_with_the_schema_error(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    content = copy.deepcopy(B0_CONTENT)
    content["recollections"][0]["present"] = ["Luis"]
    seed_brief(session_factory, novel_id, content)

    body = _confirm(client, auth_headers, novel_id)

    assert any(item["type"] == "schema_error" for item in body["detail"])


def test_confirming_sends_a_schema_brief_score_of_0_with_the_problems_in_the_comment(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    telemetry: object,
) -> None:
    from story_maker.observability.null import NullObservability

    assert isinstance(telemetry, NullObservability)
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    content = copy.deepcopy(B0_CONTENT)
    content["dedication"] = ""
    seed_brief(session_factory, novel_id, content)

    _confirm(client, auth_headers, novel_id)

    trace = telemetry.traces[f"interview:{novel_id}"]
    scores = [s for s in trace.scores if s.name == "schema-brief"]
    assert [s.value for s in scores] == [0]
    comment = scores[0].comment
    assert comment is not None
    assert "dedication" in comment

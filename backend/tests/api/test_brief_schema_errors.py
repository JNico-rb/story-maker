"""Comprobación de schema: bloquea la confirmación con 422 (008-C13)."""

from __future__ import annotations

import copy

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from .briefs import B0_CONTENT, seed_brief


def test_an_unknown_present_blocks_confirmation_with_422(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    content = copy.deepcopy(B0_CONTENT)
    content["recollections"][0]["present"] = ["Luis"]
    seed_brief(session_factory, novel_id, content)

    confirm = client.post(f"/api/novels/{novel_id}/brief/confirm", headers=auth_headers)

    assert confirm.status_code == 422
    assert any("Presente desconocido" in item["msg"] for item in confirm.json()["detail"])

    body = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()
    assert any("Presente desconocido" in e["message"] for e in body["schema_errors"])

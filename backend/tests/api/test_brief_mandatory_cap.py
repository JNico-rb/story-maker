"""Cota de elementos obligatorios (008-C12)."""

from __future__ import annotations

import copy

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from .briefs import B0_CONTENT, seed_brief


def _with_mandatory_close_ones(count: int) -> dict[str, object]:
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
        for i in range(count)
    ]
    return content


def test_eight_mandatory_elements_has_no_problem(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    # B0 ya cuenta 2 (nombre y recuerdo); 6 allegados obligatorios más dan 8.
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, _with_mandatory_close_ones(6))

    confirm = client.post(f"/api/novels/{novel_id}/brief/confirm", headers=auth_headers)

    assert confirm.status_code == 200


def test_nine_mandatory_elements_is_rejected_with_9_of_8(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, _with_mandatory_close_ones(7))

    confirm = client.post(f"/api/novels/{novel_id}/brief/confirm", headers=auth_headers)

    assert confirm.status_code == 422
    assert any("9 de 8" in item["msg"] for item in confirm.json()["detail"])


def test_a_non_mandatory_close_one_does_not_count(
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
            "mandatory": False,
        }
        for i in range(20)
    ]
    seed_brief(session_factory, novel_id, content)

    confirm = client.post(f"/api/novels/{novel_id}/brief/confirm", headers=auth_headers)

    assert confirm.status_code == 200

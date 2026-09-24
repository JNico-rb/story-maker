"""Datos faltantes, uno por campo (008-C09)."""

from __future__ import annotations

import copy
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from .briefs import B0_CONTENT, seed_brief


def _without(**overrides: Any) -> dict[str, Any]:
    content = copy.deepcopy(B0_CONTENT)
    for key, value in overrides.items():
        content[key] = value
    return content


def _recipient(**overrides: Any) -> dict[str, Any]:
    content = copy.deepcopy(B0_CONTENT)
    content["recipient"] = {**content["recipient"], **overrides}
    return content


@pytest.mark.parametrize(
    ("content", "expected_missing"),
    [
        (_recipient(name=""), "name"),
        (_recipient(age=None), "age"),
        (_recipient(traits=[]), "traits"),
        (_without(recollections=[]), "recollections"),
        (_without(occasion=None), "occasion"),
        (_without(genre=None), "genre"),
        (_without(tone=None), "tone"),
        (_without(length=None), "length"),
        (_without(dedication=""), "dedication"),
        (_without(dedication="   "), "dedication"),
        (_without(banned_asked=False), "banned_asked"),
    ],
)
def test_removing_one_field_makes_exactly_that_field_missing(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    content: dict[str, Any],
    expected_missing: str,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, content)

    body = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()
    assert body["missing_fields"] == [expected_missing]

    confirm = client.post(f"/api/novels/{novel_id}/brief/confirm", headers=auth_headers)
    assert confirm.status_code == 422
    assert any(expected_missing in str(item["loc"]) for item in confirm.json()["detail"])


def test_an_empty_draft_is_missing_all_ten_fields(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]

    body = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()

    assert body["missing_fields"] == [
        "name",
        "age",
        "traits",
        "recollections",
        "occasion",
        "genre",
        "tone",
        "length",
        "dedication",
        "banned_asked",
    ]


def test_b0_has_nothing_missing_and_confirms(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)

    body = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()
    assert body["missing_fields"] == []

    confirm = client.post(f"/api/novels/{novel_id}/brief/confirm", headers=auth_headers)
    assert confirm.status_code == 200
    assert confirm.json()["status"] == "confirmed"

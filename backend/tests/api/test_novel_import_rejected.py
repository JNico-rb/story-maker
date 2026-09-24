"""Importación rechazada antes de extraer (008-C29)."""

from __future__ import annotations

import copy
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import FakeAgent
from story_maker.store.models import AuditLog, ExtractedFact, FreeText, Novel

from .briefs import B0_CONTENT


def _content(**overrides: Any) -> dict[str, Any]:
    content = copy.deepcopy(B0_CONTENT)
    content.update(overrides)
    return content


def _recipient(**overrides: Any) -> dict[str, Any]:
    content = copy.deepcopy(B0_CONTENT)
    content["recipient"] = {**content["recipient"], **overrides}
    return content


def _nine_mandatory_close_ones() -> dict[str, Any]:
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
    return content


def _unknown_present() -> dict[str, Any]:
    content = copy.deepcopy(B0_CONTENT)
    content["recollections"][0]["present"] = ["Luis"]
    return content


@pytest.mark.parametrize(
    ("body", "expected_type_or_msg"),
    [
        pytest.param(
            {**B0_CONTENT, "not_a_brief_field": "x"}, "extra_forbidden", id="unknown-field"
        ),
        pytest.param(_content(genre="ciencia ficción"), "literal_error", id="unknown-genre"),
        pytest.param(_recipient(age="cuarenta"), "int_parsing", id="age-not-a-number"),
        pytest.param(
            {**B0_CONTENT, "free_texts": ["x" * 20001]}, "20000 caracteres", id="free-text-too-long"
        ),
        pytest.param(_content(dedication=""), "missing_field", id="missing-dedication"),
        pytest.param(
            {**_recipient(age=17), "occasion": "wedding"}, "contradiction", id="age-17-wedding"
        ),
        pytest.param(_nine_mandatory_close_ones(), "mandatory_cap", id="nine-mandatory"),
        pytest.param(_unknown_present(), "schema_error", id="unknown-present"),
        pytest.param(_content(banned_asked=False), "missing_field", id="banned-not-asked"),
    ],
)
def test_each_invalid_brief_is_rejected_and_creates_nothing(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
    body: dict[str, Any],
    expected_type_or_msg: str,
) -> None:
    response = client.post("/api/novels", json=body, headers=auth_headers)

    assert response.status_code == 422, response.json()
    detail = response.json()["detail"]
    assert detail
    assert any(
        expected_type_or_msg in str(item.get("type", ""))
        or expected_type_or_msg in str(item.get("msg", ""))
        for item in detail
    ), detail

    with session_factory() as session:
        assert session.query(Novel).count() == 0
        assert session.query(FreeText).count() == 0
        assert session.query(ExtractedFact).count() == 0
        assert session.query(AuditLog).count() == 0
    assert fake.sessions == []

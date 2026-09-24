"""Importar y confirmar deciden igual (008-I1): con los briefs de las tablas de 008-C09 a
008-C13, la importación rechaza con exactamente los problemas con que rechaza la confirmación,
y las dos aceptan los mismos briefs."""

from __future__ import annotations

import copy
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.store.models import BannedTerm

from .briefs import B0_CONTENT, seed_brief


def _recipient(**overrides: Any) -> dict[str, Any]:
    content = copy.deepcopy(B0_CONTENT)
    content["recipient"] = {**content["recipient"], **overrides}
    return content


def _without(**overrides: Any) -> dict[str, Any]:
    content = copy.deepcopy(B0_CONTENT)
    content.update(overrides)
    return content


def _mandatory_close_ones(count: int) -> dict[str, Any]:
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


def _unknown_present() -> dict[str, Any]:
    content = copy.deepcopy(B0_CONTENT)
    content["recollections"][0]["present"] = ["Luis"]
    return content


CASES: list[tuple[str, dict[str, Any], bool]] = [
    # 008-C09: datos faltantes, uno por campo.
    ("missing-name", _recipient(name=""), False),
    ("missing-age", _recipient(age=None), False),
    ("missing-traits", _recipient(traits=[]), False),
    ("missing-recollections", _without(recollections=[]), False),
    ("missing-occasion", _without(occasion=None), False),
    ("missing-genre", _without(genre=None), False),
    ("missing-tone", _without(tone=None), False),
    ("missing-length", _without(length=None), False),
    ("missing-dedication", _without(dedication=""), False),
    ("missing-banned-asked", _without(banned_asked=False), False),
    # 008-C10: contradicciones C1-C5.
    ("c1-age-genre", {**_recipient(age=11), "genre": "romance"}, False),
    ("c2-age-tone", {**_recipient(age=11), "tone": "unsettling"}, False),
    ("c3-age-occasion", {**_recipient(age=17), "occasion": "wedding"}, False),
    ("c4-age-birth-date", _recipient(age=40, birth_date="2020-01-01"), False),
    (
        "c5-recollection-age",
        _without(recollections=[{**B0_CONTENT["recollections"][0], "age": 90}]),
        False,
    ),
    # 008-C12: cota de elementos obligatorios.
    ("mandatory-cap-ok", _mandatory_close_ones(6), True),
    ("mandatory-cap-exceeded", _mandatory_close_ones(7), False),
    # 008-C13: comprobación de schema.
    ("unknown-present", _unknown_present(), False),
    # Un brief válido: las dos vías aceptan.
    ("b0-valid", copy.deepcopy(B0_CONTENT), True),
]


@pytest.mark.parametrize(("case_id", "content", "accepted"), CASES, ids=[c[0] for c in CASES])
def test_import_and_confirm_agree(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    case_id: str,
    content: dict[str, Any],
    accepted: bool,
) -> None:
    import_response = client.post("/api/novels", json=content, headers=auth_headers)

    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, content)
    confirm_response = client.post(f"/api/novels/{novel_id}/brief/confirm", headers=auth_headers)

    if accepted:
        assert import_response.status_code == 201, import_response.json()
        assert confirm_response.status_code == 200, confirm_response.json()
    else:
        assert import_response.status_code == 422, import_response.json()
        assert confirm_response.status_code == 422, confirm_response.json()
        # Mismos problemas exactos (mismo cálculo, 008-I1): ignora el `loc` de la importación,
        # que empieza en el cuerpo de la petición en vez de en `brief`.
        import_problems = {(p["msg"], p["type"]) for p in import_response.json()["detail"]}
        confirm_problems = {(p["msg"], p["type"]) for p in confirm_response.json()["detail"]}
        assert import_problems == confirm_problems


def test_a_banned_dedication_is_rejected_by_both_with_c6(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    content = copy.deepcopy(B0_CONTENT)
    content["dedication"] = "Para Marta, con Pedro cerca"

    import_body = {**content, "banned_entries": [{"term": "Pedro", "type": "word", "keywords": []}]}
    import_response = client.post("/api/novels", json=import_body, headers=auth_headers)

    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, content)
    with session_factory() as session:
        session.add(
            BannedTerm(
                level="novel",
                user_id=None,
                novel_id=novel_id,
                term="Pedro",
                type="word",
                keywords=None,
                normalized="pedro",
            )
        )
        session.commit()
    confirm_response = client.post(f"/api/novels/{novel_id}/brief/confirm", headers=auth_headers)

    assert import_response.status_code == 422
    assert confirm_response.status_code == 422
    assert any(p["type"] == "contradiction" for p in import_response.json()["detail"])
    assert any(p["type"] == "contradiction" for p in confirm_response.json()["detail"])

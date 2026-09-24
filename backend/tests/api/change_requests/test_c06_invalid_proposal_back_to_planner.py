"""014-C06 — El código valida la propuesta y una inválida vuelve al planner con sus defectos
(RT4)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, FakeAgent, Script
from story_maker.store import models
from story_maker.store.session import unit_of_work
from story_maker.store.version_copy import copy_version

from .conftest import (
    NOW,
    F,
    build_f,
    fact_selection,
    fragment_selection,
    headers,
    planner_message,
    propose,
    rename,
)

REQUEST = "el perro se llama Nala"

Proposal = Callable[[F, sessionmaker[Session]], dict[str, Any]]


def _fact_of_another_novel(f: F, sf: sessionmaker[Session]) -> dict[str, Any]:
    return rename(build_f(sf).toby_name_fact, "Nala")


def _fact_of_another_version(f: F, sf: sessionmaker[Session]) -> dict[str, Any]:
    with unit_of_work(sf) as uow:
        draft = copy_version(uow, f.v1_id, now=NOW).version.id
    with sf() as session:
        fact = session.query(models.Fact).filter_by(version_id=draft, attribute="name").first()
        assert fact is not None
        return rename(fact.id, "Nala")


def _new_fact(subject_id: Callable[[F], int], attribute: str) -> Proposal:
    def proposal(f: F, sf: sessionmaker[Session]) -> dict[str, Any]:
        return {
            "new_fact": {
                "subject_type": "character",
                "subject_id": subject_id(f),
                "attribute": attribute,
                "value": "teme las tormentas",
            }
        }

    return proposal


INVALID_ROWS: list[tuple[str, dict[str, Any], Proposal, str]] = [
    (
        "hecho-de-otra-novela",
        {},
        _fact_of_another_novel,
        "hecho inexistente en la versión vigente",
    ),
    (
        "hecho-de-otra-version",
        {},
        _fact_of_another_version,
        "hecho inexistente en la versión vigente",
    ),
    ("valor-vacio", {}, lambda f, sf: rename(f.toby_name_fact, ""), "el cambio no cambia nada"),
    ("valor-igual", {}, lambda f, sf: rename(f.toby_name_fact, "Toby"), "el cambio no cambia nada"),
    (
        "prohibida-en-el-valor",
        {},
        lambda f, sf: rename(f.toby_name_fact, "Zoquete"),
        "prohibida en el valor nuevo: término=zoquete, nivel=global",
    ),
    ("sujeto-inexistente", {}, _new_fact(lambda f: 9999, "trait"), "sujeto inexistente"),
    (
        "atributo-fuera-del-vocabulario",
        {},
        _new_fact(lambda f: f.toby_id, "color"),
        "atributo fuera del vocabulario",
    ),
    (
        "hecho-del-brief-no-seleccionado",
        {},
        lambda f, sf: {
            "changes": [
                {"fact_id": f.toby_name_fact, "new_value": "Nala"},
                {"fact_id": f.dessert_fact, "new_value": "tarta de queso"},
            ]
        },
        "hecho del brief fuera de la selección",
    ),
    (
        "fragmento-donde-no-aparece",
        {"chapter": 3},
        lambda f, sf: rename(f.toby_name_fact, "Nala"),
        "hecho del brief fuera de la selección",
    ),
]


def _selection(f: F, fragment: dict[str, Any]) -> dict[str, Any]:
    if fragment:
        return fragment_selection(fragment["chapter"])
    return fact_selection(f.toby_name_fact)


def _valid_second(f: F, fragment: dict[str, Any]) -> dict[str, Any]:
    """La entrega de 014-C01; con el fragmento del capítulo 3, donde el perro no aparece, esa
    tampoco es válida: la segunda cambia el postre de Ada, que sí aparece en él."""
    if fragment:
        return rename(f.dessert_fact, "tarta de queso")
    return rename(f.toby_name_fact, "Nala")


def _attempts(sf: sessionmaker[Session], request_id: int) -> list[tuple[int, str | None]]:
    with sf() as session:
        rows = session.query(models.Attempt).filter_by(change_request_id=request_id)
        return sorted((a.number, a.outcome) for a in rows if a.evaluable == "change")


@pytest.mark.parametrize(
    ("fragment", "first", "defect"),
    [row[1:] for row in INVALID_ROWS],
    ids=[row[0] for row in INVALID_ROWS],
)
def test_an_invalid_proposal_is_a_rewrite_and_a_new_planner_session_receives_its_defect(
    client: TestClient,
    f: F,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    fragment: dict[str, Any],
    first: Proposal,
    defect: str,
) -> None:
    propose(fake, first(f, session_factory), _valid_second(f, fragment))

    response = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": _selection(f, fragment), "request": REQUEST},
        headers=headers(f.user_a),
    )

    assert response.status_code == 201, response.text
    assert _attempts(session_factory, response.json()["id"]) == [(1, "rewrite"), (2, "accept")]
    planners = [s for s in fake.sessions if s.request.role == "planner"]
    assert [(s.request.mode, s.request.tools[0].name) for s in planners] == [
        ("change", "propose_change"),
        ("change", "propose_change"),
    ]
    second = planner_message(fake, 1)
    assert second["selection"] == _selection(f, fragment)
    assert second["request"] == REQUEST
    assert second["story_bible"]["version_id"] == f.v1_id
    assert any(defect in d.lower() for d in second["defects"]), second["defects"]
    assert "defects" not in planner_message(fake, 0)


def test_a_banned_new_value_leaves_a_deny_with_origin_change_request_in_the_tool_field(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    propose(fake, rename(f.toby_name_fact, "Zoquete"), rename(f.toby_name_fact, "Nala"))

    client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": REQUEST},
        headers=headers(f.user_a),
    )

    with session_factory() as session:
        denials = (
            session.query(models.AuditLog)
            .filter_by(novel_id=f.novel_id, origin="change_request", decision="deny")
            .all()
        )
        assert [d.detail[0]["location"] for d in denials] == ["tool_field"]  # type: ignore[index]


def test_changing_an_invented_fact_outside_the_selection_is_valid(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    propose(
        fake,
        {
            "changes": [
                {"fact_id": f.toby_name_fact, "new_value": "Nala"},
                {"fact_id": f.invented_fact, "new_value": "come manzanas"},
            ]
        },
    )

    response = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": REQUEST},
        headers=headers(f.user_a),
    )

    assert response.status_code == 201, response.text
    assert _attempts(session_factory, response.json()["id"]) == [(1, "accept")]
    assert len(fake.sessions) == 1


SCHEMA_ERRORS: list[tuple[str, Callable[[F], dict[str, Any]]]] = [
    (
        "el-mismo-hecho-dos-veces",
        lambda f: {
            "changes": [
                {"fact_id": f.toby_name_fact, "new_value": "Nala"},
                {"fact_id": f.toby_name_fact, "new_value": "Luna"},
            ]
        },
    ),
    (
        "cambios-y-hecho-nuevo",
        lambda f: {
            **rename(f.toby_name_fact, "Nala"),
            "new_fact": {
                "subject_type": "character",
                "subject_id": f.toby_id,
                "attribute": "trait",
                "value": "teme las tormentas",
            },
        },
    ),
    ("nada", lambda f: {}),
]


@pytest.mark.parametrize(
    "first", [row[1] for row in SCHEMA_ERRORS], ids=[row[0] for row in SCHEMA_ERRORS]
)
def test_a_schema_error_goes_back_in_the_same_session_and_counts_as_an_attempt(
    client: TestClient,
    f: F,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    first: Callable[[F], dict[str, Any]],
) -> None:
    steps = (
        Call("propose_change", first(f)),
        Call("propose_change", rename(f.toby_name_fact, "Nala")),
    )
    fake.script("planner", "change", Script(steps=steps))

    response = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": REQUEST},
        headers=headers(f.user_a),
    )

    assert response.status_code == 201, response.text
    assert _attempts(session_factory, response.json()["id"]) == [(1, "rewrite"), (2, "accept")]
    assert len(fake.sessions) == 1
    assert fake.sessions[0].reads[0].startswith("Entrada inválida para propose_change")

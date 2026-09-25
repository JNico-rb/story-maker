"""014-C02 — Los afectados son los usos, más el valor antiguo literal, más el capítulo del
fragmento. Cada fila es una variación de F con una sola causa."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import FakeAgent

from .conftest import F, build_f, fact_selection, fragment_selection, headers, propose, rename

NEW_TRAIT = "teme las tormentas"


def _new_trait(f: F) -> dict[str, Any]:
    return {
        "new_fact": {
            "subject_type": "character",
            "subject_id": f.toby_id,
            "attribute": "trait",
            "value": NEW_TRAIT,
        }
    }


Row = tuple[
    Callable[[F], dict[str, Any]],  # selección
    Callable[[F], dict[str, Any]],  # propuesta
    dict[int, str],  # texto añadido por capítulo
    dict[int, str],  # títulos
    list[int],  # afectados
]

ROWS: dict[str, Row] = {
    "hecho del perro": (
        lambda f: fact_selection(f.toby_name_fact),
        lambda f: rename(f.toby_name_fact, "Nala"),
        {},
        {},
        [2, 5, 7],
    ),
    "fragmento del capítulo 9": (
        lambda f: fragment_selection(9),
        lambda f: rename(f.toby_name_fact, "Nala"),
        {},
        {},
        [2, 5, 7, 9],
    ),
    "mayúsculas y acentos": (
        lambda f: fact_selection(f.toby_name_fact),
        lambda f: rename(f.toby_name_fact, "Nala"),
        {3: " Llega TOBY.", 4: " Corre Tóby."},
        {},
        [2, 3, 4, 5, 7],
    ),
    "palabras completas": (
        lambda f: fact_selection(f.toby_name_fact),
        lambda f: rename(f.toby_name_fact, "Nala"),
        {6: " Viene Tobías.", 10: " Van a Tobyland."},
        {},
        [2, 5, 7],
    ),
    "solo en el título": (
        lambda f: fact_selection(f.toby_name_fact),
        lambda f: rename(f.toby_name_fact, "Nala"),
        {},
        {8: "Toby en la playa"},
        [2, 5, 7, 8],
    ),
    "varias palabras como secuencia": (
        lambda f: fact_selection(f.dessert_fact),
        lambda f: rename(f.dessert_fact, "tarta de queso"),
        {6: " Comen Tarta   de manzana.", 4: " Compran una manzana."},
        {},
        [3, 6],
    ),
    "dos hechos desde un fragmento": (
        lambda f: fragment_selection(5),
        lambda f: {
            "changes": [
                {"fact_id": f.toby_name_fact, "new_value": "Nala"},
                {"fact_id": f.dessert_fact, "new_value": "tarta de queso"},
            ]
        },
        {},
        {},
        [2, 3, 5, 7],
    ),
    "hecho inventado": (
        lambda f: fact_selection(f.invented_fact),
        lambda f: rename(f.invented_fact, "come manzanas"),
        {},
        {},
        [],
    ),
    "hecho nuevo desde un fragmento": (
        lambda f: fragment_selection(4),
        _new_trait,
        {},
        {},
        [4],
    ),
    "hecho nuevo desde un hecho": (
        lambda f: fact_selection(f.toby_name_fact),
        _new_trait,
        {},
        {},
        [],
    ),
}


@pytest.mark.parametrize("row", list(ROWS), ids=list(ROWS))
def test_the_affected_chapters_are_the_usages_the_literal_old_value_and_the_fragment_chapter(
    row: str, client: TestClient, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    selection, proposal, extra_text, titles, expected = ROWS[row]
    f = build_f(session_factory, extra_text=extra_text, titles=titles)
    propose(fake, proposal(f))

    response = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": selection(f), "request": "un cambio"},
        headers=headers(f.user_a),
    )

    assert response.status_code == 201, response.text
    assert response.json()["affected_chapters"] == expected


def test_a_new_fact_proposal_is_returned_with_its_subject_attribute_and_value(
    client: TestClient, fake: FakeAgent, f: F
) -> None:
    propose(fake, _new_trait(f))

    response = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fragment_selection(4), "request": "el perro teme las tormentas"},
        headers=headers(f.user_a),
    )

    assert response.status_code == 201, response.text
    assert response.json()["proposal"] == {"new_fact": f"Toby · trait: {NEW_TRAIT}"}

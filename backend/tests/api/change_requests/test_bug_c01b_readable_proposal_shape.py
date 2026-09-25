"""014-bug-C01b — La propuesta de la API web sale con la forma que lee la SPA congelada
(027-C03; `architecture.md` §15.7, «Forma de la propuesta»): `fact`/`old_value`/`new_value` en
texto, o `new_fact` como una sola frase; la clave que no aplica no aparece y ninguna lleva un
objeto. Lo guardado en la base (y lo que entrega el servidor MCP) no cambia."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import FakeAgent
from story_maker.store import models

from .conftest import F, fact_selection, fragment_selection, headers, propose, rename

NEW_TRAIT = "teme las tormentas"


def test_a_single_fact_change_reads_as_subject_attribute_and_plain_text_values(
    client: TestClient, f: F, fake: FakeAgent
) -> None:
    propose(fake, rename(f.toby_name_fact, "Nala"))

    response = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": "el perro se llama Nala"},
        headers=headers(f.user_a),
    )

    assert response.status_code == 201, response.text
    assert response.json()["proposal"] == {
        "fact": "Toby · name",
        "old_value": "Toby",
        "new_value": "Nala",
    }


def test_several_fact_changes_join_each_field_with_semicolons_in_order(
    client: TestClient, f: F, fake: FakeAgent
) -> None:
    propose(
        fake,
        {
            "changes": [
                {"fact_id": f.toby_name_fact, "new_value": "Nala"},
                {"fact_id": f.dessert_fact, "new_value": "tarta de queso"},
            ]
        },
    )

    response = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fragment_selection(5), "request": "cambia el perro y el postre"},
        headers=headers(f.user_a),
    )

    assert response.status_code == 201, response.text
    assert response.json()["proposal"] == {
        "fact": "Toby · name; Ada · trait",
        "old_value": "Toby; tarta de manzana",
        "new_value": "Nala; tarta de queso",
    }


def test_a_new_fact_reads_as_one_sentence_with_subject_attribute_and_value(
    client: TestClient, f: F, fake: FakeAgent
) -> None:
    propose(
        fake,
        {
            "new_fact": {
                "subject_type": "character",
                "subject_id": f.toby_id,
                "attribute": "trait",
                "value": NEW_TRAIT,
            }
        },
    )

    response = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fragment_selection(4), "request": "el perro teme las tormentas"},
        headers=headers(f.user_a),
    )

    assert response.status_code == 201, response.text
    assert response.json()["proposal"] == {"new_fact": f"Toby · trait: {NEW_TRAIT}"}


def test_the_stored_proposal_keeps_the_internal_shape_with_fact_ids(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    propose(fake, rename(f.toby_name_fact, "Nala"))

    response = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": "el perro se llama Nala"},
        headers=headers(f.user_a),
    )

    with session_factory() as session:
        row = session.get_one(models.ChangeRequest, response.json()["id"])
        assert row.proposal == {
            "changes": [{"fact_id": f.toby_name_fact, "old_value": "Toby", "new_value": "Nala"}],
            "new_fact": None,
        }


def test_a_world_fact_change_reads_as_mundo_and_attribute(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    with session_factory.begin() as session:
        world = models.Fact(
            version_id=f.v1_id,
            subject_type="world",
            attribute="season",
            value="otoño",
            origin="brief",
            mandatory=False,
        )
        session.add(world)
        session.flush()
        world_id = world.id
    propose(fake, rename(world_id, "primavera"))

    response = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(world_id), "request": "que sea en primavera"},
        headers=headers(f.user_a),
    )

    assert response.status_code == 201, response.text
    assert response.json()["proposal"] == {
        "fact": "mundo · season",
        "old_value": "otoño",
        "new_value": "primavera",
    }

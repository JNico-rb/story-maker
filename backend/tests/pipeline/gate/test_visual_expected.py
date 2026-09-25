"""017-C01 · La estructura esperada sale de la candidata."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import NOW, Seed
from tests.pipeline.gate.conftest import publish_as
from tests.pipeline.gate.visual import (
    DEDICATION,
    EXPECTED,
    TITLE,
    chapter_text,
    chapter_title,
    name_fact,
    seed_visual,
)

from story_maker.pipeline.gate.visual import expected_structure
from story_maker.store.models import Character
from story_maker.store.session import unit_of_work
from story_maker.store.story_bible import change_fact_value
from story_maker.store.version_copy import copy_version


def test_the_expected_structure_comes_from_the_candidate_cover_index_chapters_and_ficha(
    session_factory: sessionmaker[Session], at_gate: Seed
) -> None:
    seed_visual(session_factory, at_gate)

    with session_factory() as session:
        expected = expected_structure(session, at_gate.version_id)

    assert (expected.cover.title, expected.cover.recipient) == (TITLE, "Marta")
    assert expected.cover.dedication == DEDICATION
    assert expected.index == tuple(range(1, 11))
    assert [(c.number, c.title, c.text) for c in expected.chapters] == [
        (n, chapter_title(n), chapter_text(n)) for n in range(1, 11)
    ]
    assert {e.name: e.chapters for e in expected.ficha} == {
        e.name: e.chapters for e in EXPECTED.ficha
    }
    assert {e.name: e.kind for e in expected.ficha} == {
        "Marta": "personaje",
        "Toby": "personaje",
        "Faro de Cabo Mayor": "lugar",
        "Villaverde": "lugar",
    }


def test_a_change_candidate_that_renames_the_dog_expects_the_new_name_never_the_base_one(
    session_factory: sessionmaker[Session], at_gate: Seed
) -> None:
    seed_visual(session_factory, at_gate)
    with session_factory() as session:
        publish_as(session, at_gate.version_id, 1)
        session.commit()
    with unit_of_work(session_factory) as uow:
        candidate = copy_version(uow, at_gate.version_id, now=NOW).version.id
    with unit_of_work(session_factory) as uow:
        toby = (
            uow.session.query(Character)
            .filter(Character.version_id == candidate, Character.canonical_name == "Toby")
            .one()
        )
        change_fact_value(uow, name_fact(uow.session, candidate, toby.id).id, "Nala")

    with session_factory() as session:
        expected = expected_structure(session, candidate)
        base = expected_structure(session, at_gate.version_id)

    names = {e.name for e in expected.ficha}
    assert "Nala" in names
    assert "Toby" not in names
    assert {e.name: e.chapters for e in expected.ficha}["Nala"] == frozenset({2, 5})
    assert "Toby" in {e.name for e in base.ficha}

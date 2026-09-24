"""Canon del brief en la candidata de generación (009-C01 a 009-C10, 009-I7).

`store` es el atajo de `conftest.py` sobre el almacén de la prueba (tipo `Store`)."""

from __future__ import annotations

import datetime as dt
from dataclasses import replace
from typing import Any

from story_maker.store import models
from story_maker.store.brief_canon import (
    NAME,
    NOMINAL_ATTRIBUTES,
    RELATIONSHIP,
    TRAIT,
    ConfirmedBrief,
)

from_brief = "brief"


def _rows(store: Any, model: Any, version_id: int) -> list[Any]:
    with store.session() as session:
        return list(session.query(model).filter(model.version_id == version_id).all())


def test_the_generation_candidate_is_born_with_the_brief_canon(
    store: Any, f1: ConfirmedBrief
) -> None:
    novel_id = store.new_novel()

    version_id = store.generation(novel_id, f1)

    with store.session() as session:
        versions = session.query(models.Version).filter_by(novel_id=novel_id).all()
    assert [v.id for v in versions] == [version_id]
    version = versions[0]
    assert version.status == "candidate"
    assert version.base_version_id is None
    assert version.number is None
    assert version.changed_chapters == []
    assert version.pdf_path is None
    assert version.created_at == store.now

    characters = _rows(store, models.Character, version_id)
    places = _rows(store, models.Place, version_id)
    facts = _rows(store, models.Fact, version_id)
    events = _rows(store, models.Event, version_id)
    assert (len(characters), len(places), len(facts), len(events)) == (4, 3, 13, 3)
    assert {c.origin for c in characters} == {from_brief}
    assert {p.origin for p in places} == {from_brief}
    assert {e.origin for e in events} == {from_brief}
    assert sorted(f.origin for f in facts) == ["brief"] * 12 + ["free_text"]
    assert [f.value for f in facts if f.origin == "free_text"] == ["la paella"]

    for model in (
        models.World,
        models.OutlineChapter,
        models.StyleSheet,
        models.Chapter,
        models.CanonCard,
    ):
        assert _rows(store, model, version_id) == [], model.__tablename__
    with store.session() as session:
        usages = (
            session.query(models.FactUsage)
            .join(models.Fact, models.Fact.id == models.FactUsage.fact_id)
            .filter(models.Fact.version_id == version_id)
            .all()
        )
    assert usages == []


def _canon(
    store: Any, brief: ConfirmedBrief, **novel: Any
) -> tuple[int, dict[str, Any], list[Any]]:
    """Candidata de generación de `brief`: su id, sus personajes por nombre y sus hechos."""
    version_id = store.generation(store.new_novel(**novel), brief)
    characters = {c.canonical_name: c for c in _rows(store, models.Character, version_id)}
    return version_id, characters, _rows(store, models.Fact, version_id)


def test_the_recipient_and_close_ones_become_characters_with_their_name_fact(
    store: Any, f1: ConfirmedBrief
) -> None:
    _, characters, facts = _canon(store, f1)

    kinds = {name: (c.type, c.species, c.origin) for name, c in characters.items()}
    assert kinds == {
        "Marta": ("recipient", "person", "brief"),
        "Toby": ("close_one", "animal", "brief"),
        "Luis": ("close_one", "person", "brief"),
        "Rosa": ("close_one", "person", "brief"),
    }
    for name, character in characters.items():
        own_nominal = [f for f in facts if f.character_id == character.id and is_nominal(f)]
        assert [(f.attribute, f.value, f.origin) for f in own_nominal] == [(NAME, name, "brief")], (
            name
        )
    assert len([f for f in facts if is_nominal(f)]) == len(characters)

    recipient = replace(f1.recipient, name="María José")
    _, accented, _ = _canon(store, replace(f1, recipient=recipient, extracted_facts=()))
    assert "María José" in accented
    assert accented["María José"].type == "recipient"


def is_nominal(fact: Any) -> bool:
    return fact.attribute in NOMINAL_ATTRIBUTES


def test_the_birth_date_is_the_declared_one_the_one_derived_from_the_age_or_none(
    store: Any, f1: ConfirmedBrief, f2: ConfirmedBrief
) -> None:
    _, characters, _ = _canon(store, f1)
    births = {name: c.birth_date for name, c in characters.items()}
    assert births == {
        "Marta": dt.date(1986, 1, 1),
        "Luis": dt.date(1989, 1, 1),
        "Toby": None,
        "Rosa": None,
    }

    _, leo, _ = _canon(store, f2)
    assert leo["Leo"].birth_date == dt.date(2000, 2, 29)

    _, later, _ = _canon(store, f1, created_at=dt.datetime(2027, 3, 1, 9, 0))
    assert later["Marta"].birth_date == dt.date(1987, 1, 1)


def _triples(facts: list[Any], characters: dict[str, Any]) -> set[tuple[str, str, str, str]]:
    names = {c.id: name for name, c in characters.items()}
    return {(names[f.character_id], f.attribute, f.value, f.origin) for f in facts}


def test_traits_relationships_and_accepted_extracted_facts_become_facts(
    store: Any, f1: ConfirmedBrief
) -> None:
    _, characters, facts = _canon(store, f1)
    triples = _triples(facts, characters)

    assert {
        ("Marta", TRAIT, "curiosa", "brief"),
        ("Marta", TRAIT, "le encanta el mar", "brief"),
        ("Toby", RELATIONSHIP, "perro", "brief"),
        ("Luis", RELATIONSHIP, "hermano", "brief"),
        ("Rosa", RELATIONSHIP, "abuela", "brief"),
        ("Marta", "comida favorita", "la paella", "free_text"),
    } <= triples
    assert not [t for t in triples if t[2] == "negro"]  # X2, sin aceptar

    imported_x1 = replace(f1.extracted_facts[0], mandatory=False)
    imported = replace(f1, extracted_facts=(imported_x1,))
    _, characters, facts = _canon(store, imported)
    x1 = [f for f in facts if f.value == "la paella"]
    assert [(f.origin, f.mandatory, f.attribute) for f in x1] == [
        ("free_text", False, "comida favorita")
    ]
    assert characters["Marta"].id == x1[0].character_id

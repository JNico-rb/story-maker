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
    RECOLLECTION,
    RELATIONSHIP,
    TRAIT,
    BriefRecollection,
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


def _events(store: Any, version_id: int) -> dict[str, dict[str, Any]]:
    """Eventos de la versión por enunciado, con su lugar y sus presentes (nombre → edad)."""
    with store.session() as session:
        places = {p.id: p.canonical_name for p in session.query(models.Place).all()}
        names = {c.id: c.canonical_name for c in session.query(models.Character).all()}
        events = session.query(models.Event).filter_by(version_id=version_id).all()
        out = {}
        for event in events:
            presents = session.query(models.EventCharacter).filter_by(event_id=event.id).all()
            out[event.statement] = {
                "row": event,
                "place": places[event.place_id],
                "present": {names[p.character_id]: p.declared_age for p in presents},
                "excluded": names.get(event.excluded_character_id or 0),
            }
        return out


def test_each_recollection_gives_its_fact_its_dated_event_and_its_place(
    store: Any, f1: ConfirmedBrief
) -> None:
    version_id, characters, facts = _canon(store, f1)
    events = _events(store, version_id)

    assert ("Marta", RECOLLECTION, "se perdió en la feria de su pueblo", "brief") in _triples(
        facts, characters
    )
    r1 = events["se perdió en la feria de su pueblo"]
    row = r1["row"]
    assert row.moment == dt.datetime(1994, 1, 1, 12, 0)
    assert r1["place"] == "la feria del pueblo"
    assert r1["present"] == {"Marta": 8, "Luis": None}
    assert (row.type, row.chapter, row.beat, row.analepsis, row.origin) == (
        "ordinary",
        None,
        None,
        True,
        "brief",
    )

    r2 = events["su primer baño en el mar"]
    assert ("Marta", RECOLLECTION, "su primer baño en el mar", "brief") in _triples(
        facts, characters
    )
    assert r2["row"].moment == dt.datetime(1990, 1, 1, 12, 0)
    assert r2["place"] == "la playa del faro"
    assert r2["present"] == {"Marta": None}


def test_an_excluding_recollection_names_its_excluded_one(store: Any, f1: ConfirmedBrief) -> None:
    version_id, _, _ = _canon(store, f1)
    events = _events(store, version_id)

    r3 = events["la abuela Rosa se marchó para siempre"]
    assert r3["row"].type == "exclusion"
    assert r3["excluded"] == "Rosa"
    assert r3["row"].moment == dt.datetime(1998, 1, 1, 12, 0)
    assert r3["place"] == "la estación"
    assert r3["present"] == {"Marta": 12, "Rosa": None}

    for statement in ("se perdió en la feria de su pueblo", "su primer baño en el mar"):
        assert (events[statement]["row"].type, events[statement]["excluded"]) == ("ordinary", None)


def test_there_is_one_brief_place_per_exact_place_name(store: Any, f1: ConfirmedBrief) -> None:
    r4 = BriefRecollection(
        "ganó un concurso de dibujo", "la feria del pueblo", element_id=11, mandatory=False, age=10
    )
    r5 = BriefRecollection(
        "montó en la noria", "La feria del pueblo", element_id=12, mandatory=False, age=9
    )
    brief = replace(f1, recollections=(*f1.recollections, r4, r5))

    version_id, _, _ = _canon(store, brief)

    places = _rows(store, models.Place, version_id)
    assert sorted(p.canonical_name for p in places) == sorted(
        ["la feria del pueblo", "La feria del pueblo", "la playa del faro", "la estación"]
    )
    assert {(p.origin, p.description) for p in places} == {("brief", "")}
    events = _events(store, version_id)
    r1_place = events["se perdió en la feria de su pueblo"]["row"].place_id
    assert events["ganó un concurso de dibujo"]["row"].place_id == r1_place
    assert events["montó en la noria"]["row"].place_id != r1_place


def test_the_dating_respects_the_calendar_limits(store: Any, f2: ConfirmedBrief) -> None:
    version_id, characters, _ = _canon(store, f2)
    moments = {s: e["row"].moment for s, e in _events(store, version_id).items()}

    birth = dt.datetime.combine(characters["Leo"].birth_date, dt.time(0, 0))
    assert moments == {
        "recuerdo a los 0": dt.datetime(2000, 2, 29, 12, 0),
        "recuerdo a los 4": dt.datetime(2004, 2, 29, 12, 0),
        "recuerdo a los 5": dt.datetime(2005, 3, 1, 12, 0),
        "recuerdo en 2000": dt.datetime(2000, 3, 1, 12, 0),
        "recuerdo en 2010": dt.datetime(2010, 1, 1, 12, 0),
    }
    assert moments["recuerdo a los 0"] > birth

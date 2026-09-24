"""Lecturas de una versión: cronología registrada y story bible (009-C23, 009-C24, 009-I3).

`store` es el atajo de `conftest.py` sobre el almacén de la prueba (tipo `Store`)."""

from __future__ import annotations

import datetime as dt
from typing import Any

from story_maker.store import models
from story_maker.store.session import unit_of_work
from story_maker.store.story_bible import PresenceEntry, read_chronology, read_story_bible

R1 = "se perdió en la feria de su pueblo"
R2 = "su primer baño en el mar"
R3 = "la abuela Rosa se marchó para siempre"
E4 = "E4: Marta y Toby en la feria"
E5 = "E5: Marta e Iris en el mercado"


def _chronology(store: Any, version_id: int) -> Any:
    with store.session() as session:
        return read_chronology(session, version_id)


def test_the_recorded_chronology_of_a_version(store: Any, f1: Any) -> None:
    v1 = store.build_v1()
    chars, places = v1.characters, v1.places

    chronology = _chronology(store, v1.version_id)

    assert [e.statement for e in chronology.events] == [R2, R1, R3, E4, E5]
    by_statement = {e.statement: e for e in chronology.events}
    r1, r3, e4, e5 = (by_statement[s] for s in (R1, R3, E4, E5))
    assert (r1.moment, r1.place_id, r1.type, r1.excluded_character_id) == (
        dt.datetime(1994, 1, 1, 12, 0),
        places["la feria del pueblo"],
        "ordinary",
        None,
    )
    assert (r1.analepsis, r1.origin, r1.chapter, r1.beat) == (True, "brief", None, None)
    assert set(r1.presences) == {
        PresenceEntry(chars["Marta"], 8),
        PresenceEntry(chars["Luis"], None),
    }
    assert (r3.type, r3.excluded_character_id) == ("exclusion", chars["Rosa"])
    assert (e4.moment, e4.place_id, e4.origin, e4.chapter, e4.beat, e4.analepsis) == (
        dt.datetime(2026, 5, 10, 18, 0),
        places["la feria del pueblo"],
        "recorded",
        1,
        2,
        False,
    )
    assert set(e4.presences) == {
        PresenceEntry(chars["Marta"], None),
        PresenceEntry(chars["Toby"], None),
    }
    assert (e5.moment, e5.place_id, e5.chapter, e5.beat) == (
        dt.datetime(2026, 5, 12, 10, 0),
        places["el mercado de datos"],
        3,
        1,
    )
    assert {(b.character_id, b.birth_date) for b in chronology.births} == {
        (chars["Marta"], dt.date(1986, 1, 1)),
        (chars["Luis"], dt.date(1989, 1, 1)),
    }
    assert chronology.novum_date == dt.date(2019, 5, 1)
    assert not [e for e in chronology.events if e.origin == "planned"]

    g_id = store.generation(store.new_novel(), f1)
    g = _chronology(store, g_id)
    assert [e.statement for e in g.events] == [R2, R1, R3]
    assert len(g.births) == 2
    assert g.novum_date is None


def test_events_with_the_same_moment_are_ordered_by_id(store: Any) -> None:
    v1 = store.build_v1()
    k_id, ids = store.copy(v1.version_id)
    feria = ids["places"][v1.places["la feria del pueblo"]]
    with unit_of_work(store.session_factory) as uow:
        for statement in ("Z: el primero en nacer", "A: el segundo en nacer"):
            uow.add(
                models.Event(
                    version_id=k_id,
                    statement=statement,
                    moment=dt.datetime(2026, 5, 11, 9, 0),
                    place_id=feria,
                    type="ordinary",
                    analepsis=False,
                    origin="recorded",
                    chapter=2,
                    beat=1,
                )
            )
            uow.session.flush()

    statements = [e.statement for e in _chronology(store, k_id).events]

    assert statements[3:6] == [E4, "Z: el primero en nacer", "A: el segundo en nacer"]


def _story_bible(store: Any, version_id: int) -> Any:
    with store.session() as session:
        return read_story_bible(session, version_id)


def test_the_story_bible_of_a_version_by_its_id(store: Any, f1: Any) -> None:
    v1 = store.build_v1()

    bible = _story_bible(store, v1.version_id)

    assert bible.version_id == v1.version_id
    assert bible.present_year == 2026
    assert bible.world is not None
    assert (bible.world.novum_scope, bible.world.novum_date) == (
        "technological",
        dt.date(2019, 5, 1),
    )
    assert bible.world.novum_description == "las IA aprendieron a soñar"
    assert bible.world.consequences == ("los sueños se comparten", "nadie duerme solo")
    characters = {c.canonical_name: c for c in bible.characters}
    assert set(characters) == {"Marta", "Toby", "Luis", "Rosa", "Iris"}
    assert (characters["Iris"].type, characters["Iris"].species) == ("invented", "artificial")
    assert characters["Marta"].birth_date == dt.date(1986, 1, 1)
    places = {p.canonical_name: p for p in bible.places}
    assert set(places) == {
        "la feria del pueblo",
        "la playa del faro",
        "la estación",
        "el mercado de datos",
    }
    assert places["el mercado de datos"].description == "un mercado de recuerdos"
    assert len(bible.facts) == 15
    chapters = {f.value: f.chapters for f in bible.facts}
    assert chapters["Marta"] == tuple(range(1, 11))
    assert chapters["Toby"] == (3, 7)
    assert chapters["la paella"] == (5,)
    assert [
        v for v, used in chapters.items() if used and v not in {"Marta", "Toby", "la paella"}
    ] == []
    assert {f.value for f in bible.facts if f.nominal} == {"Marta", "Toby", "Luis", "Rosa", "Iris"}
    x1 = next(f for f in bible.facts if f.value == "la paella")
    assert (x1.origin, x1.mandatory, x1.personal_element_id, x1.attribute) == (
        "free_text",
        True,
        10,
        "comida favorita",
    )
    assert bible.chronology == _chronology(store, v1.version_id)

    g_id = store.generation(store.new_novel(), f1)
    g = _story_bible(store, g_id)
    assert g.world is None
    assert (len(g.characters), len(g.places), len(g.facts)) == (4, 3, 13)
    assert all(f.chapters == () for f in g.facts)


def _own_ids(store: Any, model: Any, version_id: int) -> set[int]:
    with store.session() as session:
        return {r.id for r in session.query(model).filter(model.version_id == version_id)}


def test_a_reading_never_returns_rows_of_another_version_or_novel(store: Any) -> None:
    a = store.build_v2()  # N1: v1 y v2
    b = store.build_v1()  # otra novela con los mismos nombres
    kb, _ = store.copy(b.version_id)
    versions = [a.v1.version_id, a.version_id, b.version_id, kb]

    for version_id in versions:
        bible = _story_bible(store, version_id)
        characters = _own_ids(store, models.Character, version_id)
        assert {c.id for c in bible.characters} == characters, version_id
        assert {p.id for p in bible.places} == _own_ids(store, models.Place, version_id)
        assert {f.id for f in bible.facts} == _own_ids(store, models.Fact, version_id)
        assert bible.world is not None
        assert {bible.world.id} == _own_ids(store, models.World, version_id)
        events = _own_ids(store, models.Event, version_id)
        assert {e.id for e in bible.chronology.events} <= events
        for event in bible.chronology.events:
            assert {p.character_id for p in event.presences} <= characters
        assert {b.character_id for b in bible.chronology.births} <= characters
        assert sum(len(f.chapters) for f in bible.facts) == 13, version_id

    assert store.current(a.v1.novel_id) == a.version_id
    assert store.current(b.novel_id) == b.version_id

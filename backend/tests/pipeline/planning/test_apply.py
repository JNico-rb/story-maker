"""El plan aceptado se aplica en una transacción (010-C20), su StyleSheet (010-C21) y sus
CanonCards iniciales (010-C22)."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.planning.conftest import ban
from tests.pipeline.planning.test_candidate import reference_brief
from tests.validators.test_outline import reference_plan

from story_maker.pipeline.planning.apply import apply_accepted_plan
from story_maker.pipeline.planning.candidate import start_generation_phase
from story_maker.pipeline.planning.plan import InventedCharacter
from story_maker.store.models import (
    CanonCard,
    Character,
    Checkpoint,
    Event,
    Fact,
    Novel,
    OutlineChapter,
    Place,
    Run,
    StyleSheet,
    World,
)
from story_maker.store.session import unit_of_work

NOW = dt.datetime(2026, 9, 24, 12, 0)


def _rows(session_factory: sessionmaker[Session], model: type, version_id: int) -> list[object]:
    with session_factory() as session:
        return list(session.scalars(select(model).filter_by(version_id=version_id)).all())


def _build_candidate(session_factory: sessionmaker[Session], run_id: int, novel_id: int) -> int:
    version = start_generation_phase(session_factory, run_id, novel_id, reference_brief(), now=NOW)
    return version.id


def _brief_origin_fingerprint(session_factory: sessionmaker[Session], version_id: int) -> object:
    with session_factory() as session:
        return {
            "characters": sorted(
                (c.canonical_name, c.type, c.origin)
                for c in session.scalars(select(Character).filter_by(version_id=version_id))
                if c.origin == "brief"
            ),
            "places": sorted(
                (p.canonical_name, p.origin)
                for p in session.scalars(select(Place).filter_by(version_id=version_id))
                if p.origin == "brief"
            ),
            "facts": sorted(
                (f.attribute, f.value, f.origin)
                for f in session.scalars(select(Fact).filter_by(version_id=version_id))
                if f.origin in ("brief", "free_text")
            ),
            "events": sorted(
                (e.statement, e.origin)
                for e in session.scalars(select(Event).filter_by(version_id=version_id))
                if e.origin == "brief"
            ),
        }


async def test_the_accepted_plan_is_applied_in_one_transaction(
    session_factory: sessionmaker[Session], run_id: int, novel_id: int
) -> None:
    version_id = _build_candidate(session_factory, run_id, novel_id)
    before = _brief_origin_fingerprint(session_factory, version_id)

    with unit_of_work(session_factory) as uow:
        run = uow.session.get(Run, run_id)
        assert run is not None
        apply_accepted_plan(uow, run, version_id, reference_plan(), now=NOW)

    (world,) = _rows(session_factory, World, version_id)
    assert (world.novum_scope, len(world.consequences)) == ("technological", 3)

    characters = {c.canonical_name: c for c in _rows(session_factory, Character, version_id)}
    places = {p.canonical_name: p for p in _rows(session_factory, Place, version_id)}
    assert (characters["Nia"].origin, characters["Nia"].species) == ("invented", "artificial")
    assert places["el puerto nuevo"].origin == "invented"

    invented_facts = [f for f in _rows(session_factory, Fact, version_id) if f.origin == "invented"]
    assert invented_facts
    assert all(not f.mandatory for f in invented_facts)

    planned_events = [e for e in _rows(session_factory, Event, version_id) if e.origin == "planned"]
    assert len(planned_events) == 2
    assert {(e.chapter, e.beat) for e in planned_events} == {(4, 1), (7, 1)}

    chapters = {c.number: c for c in _rows(session_factory, OutlineChapter, version_id)}
    assert len(chapters) == 10
    assert chapters[1].assigned_elements == [
        "marta-name",
        "mar-trait",
        "toby-name",
        "R1",
        "H1",
    ]

    assert len(_rows(session_factory, StyleSheet, version_id)) == 1
    with session_factory() as session:
        novel = session.get(Novel, novel_id)
        assert novel is not None
        assert novel.title == "El verano de Marta"
        run = session.get(Run, run_id)
        assert run is not None
        assert run.phase == "writing"
        (checkpoint,) = session.scalars(select(Checkpoint).filter_by(run_id=run_id)).all()
        assert checkpoint.chapter == 0

    assert _brief_origin_fingerprint(session_factory, version_id) == before


async def test_the_style_sheet_carries_the_age_band_and_the_banned_topics(
    session_factory: sessionmaker[Session], run_id: int, novel_id: int, user_id: int
) -> None:
    ban(
        session_factory,
        level="novel",
        term="divorcio",
        type_="topic",
        keywords=["divorcio", "separación"],
        novel_id=novel_id,
    )
    ban(
        session_factory,
        level="user",
        term="hospitales",
        type_="topic",
        keywords=["hospital", "urgencias"],
        user_id=user_id,
    )
    ban(session_factory, level="novel", term="Julián", novel_id=novel_id)
    version_id = _build_candidate(session_factory, run_id, novel_id)

    with unit_of_work(session_factory) as uow:
        run = uow.session.get(Run, run_id)
        assert run is not None
        apply_accepted_plan(uow, run, version_id, reference_plan(), now=NOW)

    (style,) = _rows(session_factory, StyleSheet, version_id)
    content = style.content
    assert content["register"] == "adult"  # Marta, 40
    terms = {entry["term"] for entry in content["avoid_lexicon"]}
    assert {"divorcio", "hospitales"} <= terms
    assert "Julián" not in terms


async def test_initial_canon_cards_get_their_from_chapter(
    session_factory: sessionmaker[Session], run_id: int, novel_id: int
) -> None:
    version_id = _build_candidate(session_factory, run_id, novel_id)
    plan = reference_plan()
    plan = plan.model_copy(
        update={"characters": (*plan.characters, InventedCharacter(name="Nadie", species="person"))}
    )

    with unit_of_work(session_factory) as uow:
        run = uow.session.get(Run, run_id)
        assert run is not None
        apply_accepted_plan(uow, run, version_id, plan, now=NOW)

    cards = _rows(session_factory, CanonCard, version_id)
    with session_factory() as session:
        characters = {c.id: c.canonical_name for c in session.scalars(select(Character))}
        places = {p.id: p.canonical_name for p in session.scalars(select(Place))}

    def name_of(card: object) -> str:
        if card.entity_type == "character":  # type: ignore[attr-defined]
            return characters[card.character_id]  # type: ignore[attr-defined]
        if card.entity_type == "place":  # type: ignore[attr-defined]
            return places[card.place_id]  # type: ignore[attr-defined]
        return "mundo"

    by_name = {name_of(c): c.from_chapter for c in cards}  # type: ignore[attr-defined]
    assert by_name["Marta"] == 1
    assert by_name["Toby"] == 1
    assert by_name["Rosa"] == 1
    assert by_name["la feria del pueblo"] == 1
    assert by_name["el aeropuerto"] == 1
    assert by_name["mundo"] == 1
    assert by_name["Nia"] == 4
    assert by_name["el puerto nuevo"] == 7
    assert by_name["Nadie"] == 1

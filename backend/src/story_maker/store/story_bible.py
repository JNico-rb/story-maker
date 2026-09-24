"""Story bible de una versión: el cambio del valor de un hecho en una candidata (009-C15, 009-C16)
y las lecturas de la story bible y de su cronología registrada (009-C23, 009-C24)."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Literal, cast

from sqlalchemy.orm import Session

from story_maker.store.brief_canon import NAME, NOMINAL_ATTRIBUTES
from story_maker.store.models import (
    Character,
    Event,
    EventCharacter,
    Fact,
    FactUsage,
    Novel,
    Place,
    Version,
    World,
)
from story_maker.store.session import UnitOfWork


def change_fact_value(uow: UnitOfWork, fact_id: int, value: str) -> Fact:
    """Cambia el valor del hecho `fact_id` en su versión (solo una candidata lo admite). Si es el
    hecho de nombre de un personaje, su nombre canónico cambia con él, en la misma transacción
    (`definitions.md` §2 Personaje). Lo usan 014 y 019 (009-I8)."""
    fact = _fact(uow.session, fact_id)
    fact.value = value
    if fact.attribute == NAME and fact.character_id is not None:
        _rename_character(uow.session, fact.character_id, value)
    return fact


def _rename_character(session: Session, character_id: int, name: str) -> None:
    character = session.get(Character, character_id)
    if character is None:
        raise LookupError(f"no existe el personaje {character_id}")
    character.canonical_name = name


def _fact(session: Session, fact_id: int) -> Fact:
    fact = session.get(Fact, fact_id)
    if fact is None:
        raise LookupError(f"no existe el hecho {fact_id}")
    return fact


EventType = Literal["ordinary", "exclusion"]
EventOrigin = Literal["brief", "planned", "recorded"]

# Lo que dice el texto, no lo que se planeó: sin los planificados (§4.5, §18).
RECORDED_ORIGINS = ("brief", "recorded")


@dataclass(frozen=True)
class PresenceEntry:
    character_id: int
    declared_age: int | None


@dataclass(frozen=True)
class EventEntry:
    id: int
    statement: str
    moment: dt.datetime
    place_id: int
    presences: tuple[PresenceEntry, ...]
    type: EventType
    excluded_character_id: int | None
    analepsis: bool
    origin: EventOrigin
    chapter: int | None
    beat: int | None


@dataclass(frozen=True)
class BirthEntry:
    character_id: int
    birth_date: dt.date  # a las 00:00 (`domain-knowledge.md` §5.2)


@dataclass(frozen=True)
class Chronology:
    """La cronología registrada de una versión (`architecture.md` §4.5): los eventos de origen
    brief y registrados, por momento y a igual momento por id; las fechas de nacimiento que hay;
    la fecha del novum, si hay mundo. La leen 007 y la API."""

    events: tuple[EventEntry, ...]
    births: tuple[BirthEntry, ...]
    novum_date: dt.date | None


def read_chronology(session: Session, version_id: int) -> Chronology:
    """La cronología registrada de la versión `version_id`, candidata o no."""
    events = (
        session.query(Event)
        .filter(Event.version_id == version_id, Event.origin.in_(RECORDED_ORIGINS))
        .order_by(Event.moment, Event.id)
        .all()
    )
    presences = _presences(session, [e.id for e in events])
    characters = (
        session.query(Character)
        .filter(Character.version_id == version_id, Character.birth_date.is_not(None))
        .order_by(Character.id)
    )
    world = session.query(World).filter(World.version_id == version_id).one_or_none()
    return Chronology(
        events=tuple(_event_entry(e, presences.get(e.id, ())) for e in events),
        births=tuple(BirthEntry(c.id, c.birth_date) for c in characters if c.birth_date),
        novum_date=world.novum_date if world else None,
    )


def _presences(session: Session, event_ids: list[int]) -> dict[int, tuple[PresenceEntry, ...]]:
    rows = (
        session.query(EventCharacter)
        .filter(EventCharacter.event_id.in_(event_ids))
        .order_by(EventCharacter.character_id)
    )
    out: dict[int, list[PresenceEntry]] = {}
    for row in rows:
        out.setdefault(row.event_id, []).append(PresenceEntry(row.character_id, row.declared_age))
    return {event_id: tuple(entries) for event_id, entries in out.items()}


def _event_entry(event: Event, presences: tuple[PresenceEntry, ...]) -> EventEntry:
    return EventEntry(
        id=event.id,
        statement=event.statement,
        moment=event.moment,
        place_id=event.place_id,
        presences=presences,
        type=cast(EventType, event.type),  # enumerado garantizado por el esquema (001)
        excluded_character_id=event.excluded_character_id,
        analepsis=event.analepsis,
        origin=cast(EventOrigin, event.origin),
        chapter=event.chapter,
        beat=event.beat,
    )


@dataclass(frozen=True)
class WorldEntry:
    id: int
    novum_description: str
    novum_scope: str
    novum_date: dt.date
    consequences: tuple[str, ...]


@dataclass(frozen=True)
class CharacterEntry:
    id: int
    type: str
    species: str
    canonical_name: str
    birth_date: dt.date | None
    origin: str


@dataclass(frozen=True)
class PlaceEntry:
    id: int
    canonical_name: str
    description: str
    origin: str


@dataclass(frozen=True)
class FactEntry:
    """Un hecho con los capítulos que lo usan, en orden ascendente; `nominal` si su valor es un
    nombre propio (`definitions.md` §2 Hecho nominal)."""

    id: int
    subject_type: str
    character_id: int | None
    place_id: int | None
    attribute: str
    value: str
    origin: str
    mandatory: bool
    personal_element_id: int | None
    nominal: bool
    chapters: tuple[int, ...]


@dataclass(frozen=True)
class StoryBible:
    """El canon de una versión (`definitions.md` §2 StoryBible): lo leen 010 a 016 por dentro,
    de cualquier versión, y la API, de las publicadas."""

    version_id: int
    present_year: int
    world: WorldEntry | None
    characters: tuple[CharacterEntry, ...]
    places: tuple[PlaceEntry, ...]
    facts: tuple[FactEntry, ...]
    chronology: Chronology


def read_story_bible(session: Session, version_id: int) -> StoryBible:
    """La story bible de la versión `version_id`, candidata o no."""
    version = session.get(Version, version_id)
    if version is None:
        raise LookupError(f"no existe la versión {version_id}")
    novel = session.get(Novel, version.novel_id)
    if novel is None:
        raise LookupError(f"no existe la novela {version.novel_id}")
    world = session.query(World).filter(World.version_id == version_id).one_or_none()
    characters = session.query(Character).filter(Character.version_id == version_id)
    places = session.query(Place).filter(Place.version_id == version_id)
    facts = session.query(Fact).filter(Fact.version_id == version_id).order_by(Fact.id).all()
    usages = _chapters_by_fact(session, [f.id for f in facts])
    return StoryBible(
        version_id=version_id,
        present_year=novel.created_at.year,
        world=_world_entry(world) if world else None,
        characters=tuple(_character_entry(c) for c in characters.order_by(Character.id)),
        places=tuple(
            PlaceEntry(p.id, p.canonical_name, p.description, p.origin)
            for p in places.order_by(Place.id)
        ),
        facts=tuple(_fact_entry(f, usages.get(f.id, ())) for f in facts),
        chronology=read_chronology(session, version_id),
    )


def _chapters_by_fact(session: Session, fact_ids: list[int]) -> dict[int, tuple[int, ...]]:
    rows = (
        session.query(FactUsage)
        .filter(FactUsage.fact_id.in_(fact_ids))
        .order_by(FactUsage.fact_id, FactUsage.chapter)
    )
    out: dict[int, list[int]] = {}
    for row in rows:
        out.setdefault(row.fact_id, []).append(row.chapter)
    return {fact_id: tuple(chapters) for fact_id, chapters in out.items()}


def _world_entry(world: World) -> WorldEntry:
    return WorldEntry(
        id=world.id,
        novum_description=world.novum_description,
        novum_scope=world.novum_scope,
        novum_date=world.novum_date,
        consequences=tuple(str(c) for c in world.consequences),
    )


def _character_entry(character: Character) -> CharacterEntry:
    return CharacterEntry(
        id=character.id,
        type=character.type,
        species=character.species,
        canonical_name=character.canonical_name,
        birth_date=character.birth_date,
        origin=character.origin,
    )


def _fact_entry(fact: Fact, chapters: tuple[int, ...]) -> FactEntry:
    return FactEntry(
        id=fact.id,
        subject_type=fact.subject_type,
        character_id=fact.character_id,
        place_id=fact.place_id,
        attribute=fact.attribute,
        value=fact.value,
        origin=fact.origin,
        mandatory=fact.mandatory,
        personal_element_id=fact.personal_element_id,
        nominal=fact.attribute in NOMINAL_ATTRIBUTES,
        chapters=chapters,
    )

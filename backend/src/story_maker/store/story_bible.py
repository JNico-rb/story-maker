"""Story bible de una versión: el cambio del valor de un hecho en una candidata (009-C15, 009-C16)
y las lecturas de la story bible y de su cronología registrada (009-C23, 009-C24)."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Literal, cast

from sqlalchemy.orm import Session

from story_maker.store.brief_canon import NAME
from story_maker.store.models import Character, Event, EventCharacter, Fact, World
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

"""Canon del brief: lo que el código escribe en la candidata de generación a partir del brief
confirmado (`architecture.md` §4.1; spec 009, 009-C01 a 009-C10).

La entrada es el brief confirmado ya resuelto a lo que la story bible necesita: cada dato lleva el
identificador de su `ElementoPersonal` y su marca de obligatorio. Quien llama (010) lo construye
desde el modelo del brief de 008.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Literal

from story_maker.store.models import Character, Event, EventCharacter, Fact, Novel, Place, Version
from story_maker.store.session import UnitOfWork

# Vocabulario de atributos de los hechos del brief (`definitions.md` §2 Hecho, §11.2).
NAME = "name"
TRAIT = "trait"
RECOLLECTION = "recollection"
RELATIONSHIP = "relationship"
NOMINAL_ATTRIBUTES = frozenset({NAME})

NOON = dt.time(12, 0)


@dataclass(frozen=True)
class BriefTrait:
    statement: str
    element_id: int
    mandatory: bool


@dataclass(frozen=True)
class BriefRecipient:
    name: str
    age: int
    name_element_id: int
    traits: tuple[BriefTrait, ...]
    birth_date: dt.date | None = None


@dataclass(frozen=True)
class BriefCloseOne:
    name: str
    relationship: str
    species: Literal["person", "animal"]
    element_id: int
    mandatory: bool
    age: int | None = None
    birth_date: dt.date | None = None


@dataclass(frozen=True)
class BriefRecollection:
    """`age` (la del destinatario) o `year`, exactamente uno; `present` y `excluded`, por nombre
    de allegado."""

    statement: str
    place: str
    element_id: int
    mandatory: bool
    age: int | None = None
    year: int | None = None
    present: tuple[str, ...] = ()
    excluded: str | None = None


@dataclass(frozen=True)
class BriefExtractedFact:
    """`subject` es el nombre del destinatario o de un allegado; solo los aceptados son del brief
    y llevan elemento personal."""

    subject: str
    attribute: str
    value: str
    accepted: bool
    mandatory: bool
    element_id: int | None = None


@dataclass(frozen=True)
class ConfirmedBrief:
    recipient: BriefRecipient
    close_ones: tuple[BriefCloseOne, ...] = ()
    recollections: tuple[BriefRecollection, ...] = ()
    extracted_facts: tuple[BriefExtractedFact, ...] = ()


def create_generation_candidate(
    uow: UnitOfWork, novel: Novel, brief: ConfirmedBrief, *, now: dt.datetime
) -> Version:
    """Crea la candidata de generación de `novel` con el canon de `brief`, en la transacción de
    `uow` (009-C10)."""
    version = Version(novel_id=novel.id, status="candidate", changed_chapters=[], created_at=now)
    uow.add(version)
    uow.session.flush()

    present_year = novel.created_at.year
    recipient = brief.recipient
    characters = {
        recipient.name: _character(
            uow,
            version,
            "recipient",
            "person",
            recipient.name,
            birth_date(present_year, recipient.age, recipient.birth_date),
        )
    }
    for close_one in brief.close_ones:
        characters[close_one.name] = _character(
            uow,
            version,
            "close_one",
            close_one.species,
            close_one.name,
            birth_date(present_year, close_one.age, close_one.birth_date),
        )
    places = [_place(uow, version, recollection.place) for recollection in brief.recollections]
    uow.session.flush()

    me = characters[recipient.name]
    _fact(uow, version, me, NAME, recipient.name, "brief")
    for trait in recipient.traits:
        _fact(uow, version, me, TRAIT, trait.statement, "brief")
    for close_one in brief.close_ones:
        character = characters[close_one.name]
        _fact(uow, version, character, NAME, close_one.name, "brief")
        _fact(uow, version, character, RELATIONSHIP, close_one.relationship, "brief")
    for recollection in brief.recollections:
        _fact(uow, version, me, RECOLLECTION, recollection.statement, "brief")
    for extracted in brief.extracted_facts:
        if extracted.accepted:
            subject = characters[extracted.subject]
            _fact(uow, version, subject, extracted.attribute, extracted.value, "free_text")

    recipient_birth = recipient.birth_date or dt.date(present_year - recipient.age, 1, 1)
    for recollection, place in zip(brief.recollections, places, strict=True):
        event = Event(
            version_id=version.id,
            statement=recollection.statement,
            moment=recollection_moment(recipient_birth, recollection.age, recollection.year),
            place_id=place.id,
            type="ordinary",
            analepsis=True,
            origin="brief",
        )
        uow.add(event)
        uow.session.flush()
        uow.add(
            EventCharacter(event_id=event.id, character_id=me.id, declared_age=recollection.age)
        )
        for name in recollection.present:
            uow.add(EventCharacter(event_id=event.id, character_id=characters[name].id))
    uow.session.flush()
    return version


def birth_date(present_year: int, age: int | None, declared: dt.date | None) -> dt.date | None:
    """La declarada; si no, el 1 de enero de (año presente - edad); sin las dos, ninguna
    (`domain-knowledge.md` §5.2)."""
    if declared is not None:
        return declared
    if age is None:
        return None
    return dt.date(present_year - age, 1, 1)


def recollection_moment(birth: dt.date, age: int | None, year: int | None) -> dt.datetime:
    """A mediodía: con edad, el día en que el destinatario la cumple; con año, su 1 de enero, o
    el día siguiente al nacimiento si es el año en que nació (`domain-knowledge.md` §5.2)."""
    if age is not None:
        day = _birthday(birth, birth.year + age)
    elif year is None:
        raise ValueError("un recuerdo lleva la edad del destinatario o el año")
    elif year == birth.year:
        day = birth + dt.timedelta(days=1)
    else:
        day = dt.date(year, 1, 1)
    return dt.datetime.combine(day, NOON)


def _birthday(birth: dt.date, year: int) -> dt.date:
    """El 29 de febrero cae el 1 de marzo en un año no bisiesto."""
    try:
        return birth.replace(year=year)
    except ValueError:
        return dt.date(year, 3, 1)


def _character(
    uow: UnitOfWork,
    version: Version,
    type_: str,
    species: str,
    name: str,
    born: dt.date | None,
) -> Character:
    character = Character(
        version_id=version.id,
        type=type_,
        species=species,
        canonical_name=name,
        birth_date=born,
        origin="brief",
    )
    uow.add(character)
    return character


def _place(uow: UnitOfWork, version: Version, name: str) -> Place:
    place = Place(version_id=version.id, canonical_name=name, description="", origin="brief")
    uow.add(place)
    return place


def _fact(
    uow: UnitOfWork, version: Version, subject: Character, attribute: str, value: str, origin: str
) -> Fact:
    fact = Fact(
        version_id=version.id,
        subject_type="character",
        character_id=subject.id,
        attribute=attribute,
        value=value,
        origin=origin,
        mandatory=False,
    )
    uow.add(fact)
    return fact

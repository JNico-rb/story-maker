"""Lo que las CanonCards leen de una versión: su story bible (009), los beats de su outline y
sus eventos planificados."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from story_maker.store.models import Event, EventCharacter, OutlineChapter
from story_maker.store.story_bible import EventEntry, FactEntry, StoryBible, read_story_bible

# (tipo de entidad, character_id, place_id): la entidad de una tarjeta.
EntityKey = tuple[str, int | None, int | None]
WORLD: EntityKey = ("world", None, None)


@dataclass(frozen=True)
class Participation:
    """Quién participa en un evento: un personaje si está presente o es su excluido; un lugar
    si el evento ocurre en él."""

    chapter: int | None
    characters: frozenset[int]
    place_id: int

    def includes(self, entity: EntityKey) -> bool:
        kind, character_id, place_id = entity
        if kind == "character":
            return character_id in self.characters
        return kind == "place" and place_id == self.place_id


def participation(event: EventEntry) -> Participation:
    present = {presence.character_id for presence in event.presences}
    return Participation(
        event.chapter, _with_excluded(present, event.excluded_character_id), event.place_id
    )


def _with_excluded(present: set[int], excluded: int | None) -> frozenset[int]:
    return frozenset(present if excluded is None else present | {excluded})


@dataclass(frozen=True)
class Canon:
    bible: StoryBible
    beats: dict[int, list[dict[str, Any]]]
    planned: tuple[Participation, ...]

    def character_name(self, character_id: int) -> str:
        return next(c.canonical_name for c in self.bible.characters if c.id == character_id)

    def place_name(self, place_id: int) -> str:
        return next(p.canonical_name for p in self.bible.places if p.id == place_id)

    def facts_of(self, entity: EntityKey) -> list[FactEntry]:
        return [fact for fact in self.bible.facts if fact_subject(fact) == entity]

    def fact_subject_of(self, fact_id: int) -> EntityKey | None:
        return next((fact_subject(f) for f in self.bible.facts if f.id == fact_id), None)


def fact_subject(fact: FactEntry) -> EntityKey:
    if fact.subject_type == "world":
        return WORLD
    return (fact.subject_type, fact.character_id, fact.place_id)


def load_canon(session: Session, version_id: int) -> Canon:
    outline = session.scalars(
        select(OutlineChapter).where(OutlineChapter.version_id == version_id)
    ).all()
    planned = session.scalars(
        select(Event).where(Event.version_id == version_id, Event.origin == "planned")
    ).all()
    present = _presences(session, [event.id for event in planned])
    return Canon(
        bible=read_story_bible(session, version_id),
        beats={o.number: cast(list[dict[str, Any]], o.beats) for o in outline},
        planned=tuple(
            Participation(
                event.chapter,
                _with_excluded(present.get(event.id, set()), event.excluded_character_id),
                event.place_id,
            )
            for event in planned
        ),
    )


def _presences(session: Session, event_ids: list[int]) -> dict[int, set[int]]:
    rows = session.scalars(select(EventCharacter).where(EventCharacter.event_id.in_(event_ids)))
    out: dict[int, set[int]] = {}
    for row in rows:
        out.setdefault(row.event_id, set()).add(row.character_id)
    return out


def entities(canon: Canon) -> Iterator[tuple[EntityKey, str]]:
    """Cada entidad de la story bible con su origen; el mundo cuenta como del brief."""
    if canon.bible.world is not None:
        yield WORLD, "brief"
    for character in canon.bible.characters:
        yield ("character", character.id, None), character.origin
    for place in canon.bible.places:
        yield ("place", None, place.id), place.origin

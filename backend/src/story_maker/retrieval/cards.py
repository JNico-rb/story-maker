"""CanonCards: la plantilla de cada entidad, su cadena y la sincronización de una versión con su
story bible (`architecture.md` §6.3, §6.4)."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from story_maker.domain.constants import CHAPTERS_PER_NOVEL
from story_maker.retrieval.embedding import EmbeddingModel
from story_maker.retrieval.vectors import fingerprint, store_vectors
from story_maker.store.models import CanonCard, Event, EventCharacter, OutlineChapter
from story_maker.store.session import UnitOfWork
from story_maker.store.story_bible import StoryBible, read_story_bible

CHAPTERS = range(1, CHAPTERS_PER_NOVEL + 1)

# (tipo de entidad, character_id, place_id): la entidad de una tarjeta.
EntityKey = tuple[str, int | None, int | None]
WORLD: EntityKey = ("world", None, None)


@dataclass(frozen=True)
class Participation:
    """Quién participa en un evento: presentes, excluido y lugar."""

    chapter: int | None
    characters: frozenset[int]
    place_id: int

    def includes(self, entity: EntityKey) -> bool:
        kind, character_id, place_id = entity
        if kind == "character":
            return character_id in self.characters
        return kind == "place" and place_id == self.place_id


@dataclass(frozen=True)
class Canon:
    """Lo que la cadena necesita de una versión: su story bible, sus beats y sus eventos
    planificados."""

    bible: StoryBible
    beats: dict[int, list[dict[str, Any]]]
    planned: tuple[Participation, ...]


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
                chapter=event.chapter,
                characters=frozenset(present.get(event.id, set()))
                | _excluded(event.excluded_character_id),
                place_id=event.place_id,
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


def _excluded(character_id: int | None) -> frozenset[int]:
    return frozenset() if character_id is None else frozenset({character_id})


def entities(canon: Canon) -> Iterator[tuple[EntityKey, str, str]]:
    """Cada entidad de la story bible: su clave, su origen y su nombre."""
    if canon.bible.world is not None:
        yield WORLD, "brief", "mundo"
    for character in canon.bible.characters:
        yield ("character", character.id, None), character.origin, character.canonical_name
    for place in canon.bible.places:
        yield ("place", None, place.id), place.origin, place.canonical_name


def _fact_subject(canon: Canon, fact_id: int) -> EntityKey | None:
    for fact in canon.bible.facts:
        if fact.id == fact_id:
            if fact.subject_type == "world":
                return WORLD
            return (fact.subject_type, fact.character_id, fact.place_id)
    return None


def appears_in_beats(canon: Canon, entity: EntityKey, chapter: int) -> bool:
    """Está entre los personajes de un beat del capítulo, participa en uno de sus eventos
    planificados o es sujeto de un hecho que un beat usa."""
    for beat in canon.beats.get(chapter, []):
        if entity[0] == "character" and entity[1] in beat.get("characters", []):
            return True
        if any(_fact_subject(canon, f) == entity for f in beat.get("facts_used", [])):
            return True
    return any(e.chapter == chapter and e.includes(entity) for e in canon.planned)


def first_chapter(canon: Canon, entity: EntityKey, origin: str) -> int | None:
    """El `desde_capitulo` de la primera tarjeta; ninguno si la entidad inventada no aparece."""
    if entity == WORLD or origin == "brief":
        return 1
    return next((c for c in CHAPTERS if appears_in_beats(canon, entity, c)), None)


def expected_cards(canon: Canon) -> dict[tuple[EntityKey, int], str]:
    """(entidad, `desde_capitulo`) → texto, para toda tarjeta de la cadena de cada entidad."""
    cards: dict[tuple[EntityKey, int], str] = {}
    for entity, origin, name in entities(canon):
        first = first_chapter(canon, entity, origin)
        if first is not None:
            cards[(entity, first)] = name
    return cards


def sync_canon_cards(uow: UnitOfWork, version_id: int, embedder: EmbeddingModel) -> None:
    """Deja las CanonCards de la versión iguales a la cadena de cada entidad, en la transacción
    del llamante; nunca confirma."""
    expected = expected_cards(load_canon(uow.session, version_id))
    fresh = [
        CanonCard(
            version_id=version_id,
            entity_type=entity[0],
            character_id=entity[1],
            place_id=entity[2],
            from_chapter=from_chapter,
            text=text,
            content_hash=fingerprint(text),
        )
        for (entity, from_chapter), text in expected.items()
    ]
    for card in fresh:
        uow.add(card)
    store_vectors(uow, fresh, embedder)

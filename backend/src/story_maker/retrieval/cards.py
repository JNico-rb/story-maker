"""CanonCards: la cadena de cada entidad y la sincronización de una versión con su story bible
(`architecture.md` §6.3, §6.4)."""

from __future__ import annotations

from sqlalchemy import select

from story_maker.domain.constants import CHAPTERS_PER_NOVEL
from story_maker.retrieval.canon import WORLD, Canon, EntityKey, entities, load_canon, participation
from story_maker.retrieval.embedding import EmbeddingModel
from story_maker.retrieval.templates import render
from story_maker.retrieval.vectors import fingerprint, store_vectors
from story_maker.store.models import CanonCard
from story_maker.store.session import UnitOfWork

CHAPTERS = range(1, CHAPTERS_PER_NOVEL + 1)
# Aceptar el último capítulo da sucesoras desde el siguiente, aunque ninguna ventana las use.
LAST_FROM_CHAPTER = CHAPTERS_PER_NOVEL + 1


def appears_in_beats(canon: Canon, entity: EntityKey, chapter: int) -> bool:
    """Está entre los personajes de un beat del capítulo, participa en uno de sus eventos
    planificados o es sujeto de un hecho que un beat usa. Los beats nombran a las entidades por
    su nombre canónico, no por id de fila: se copian tal cual (`architecture.md` §18)."""
    name = canon.name_of(entity)
    for beat in canon.beats.get(chapter, []):
        if entity[0] == "character" and name in beat.get("characters", []):
            return True
        if any(used.get("subject") == name for used in beat.get("facts_used", [])):
            return True
    return any(e.chapter == chapter and e.includes(entity) for e in canon.planned)


def appears_recorded(canon: Canon, entity: EntityKey, chapter: int) -> bool:
    """La regla de la `FichaDePersonajes`: tiene un `UsoDeHecho` en el capítulo o participa en
    uno de sus eventos registrados."""
    if any(chapter in fact.chapters for fact in canon.facts_of(entity)):
        return True
    return any(
        event.origin == "recorded"
        and event.chapter == chapter
        and participation(event).includes(entity)
        for event in canon.bible.chronology.events
    )


def first_chapter(canon: Canon, entity: EntityKey, origin: str) -> int | None:
    """El `desde_capitulo` de la primera tarjeta: 1 si es del brief o es el mundo; si es
    inventada, el menor entre el primer capítulo en cuyos beats aparece y el siguiente al primero
    en que aparece registrada; ninguno si no aparece."""
    if entity == WORLD or origin == "brief":
        return 1
    in_beats = (c for c in CHAPTERS if appears_in_beats(canon, entity, c))
    after_recorded = (c + 1 for c in CHAPTERS if appears_recorded(canon, entity, c))
    return min((next(in_beats, None), next(after_recorded, None)), key=_none_last)


def _none_last(chapter: int | None) -> tuple[bool, int]:
    return (chapter is None, chapter or 0)


def chain(canon: Canon, entity: EntityKey, origin: str) -> dict[int, str]:
    """`desde_capitulo` → texto: la primera tarjeta y una sucesora en cada *d* cuya plantilla
    difiere de la de *d* - 1."""
    first = first_chapter(canon, entity, origin)
    if first is None:
        return {}
    cards = {first: render(canon, entity, first)}
    previous = cards[first]
    for chapter in range(first + 1, LAST_FROM_CHAPTER + 1):
        text = render(canon, entity, chapter)
        if text != previous:
            cards[chapter] = text
        previous = text
    return cards


def expected_cards(canon: Canon) -> dict[tuple[EntityKey, int], str]:
    """(entidad, `desde_capitulo`) → texto, para toda tarjeta de la cadena de cada entidad."""
    return {
        (entity, from_chapter): text
        for entity, origin in entities(canon)
        for from_chapter, text in chain(canon, entity, origin).items()
    }


def sync_canon_cards(uow: UnitOfWork, version_id: int, embedder: EmbeddingModel) -> None:
    """Deja las CanonCards de la versión iguales a la cadena de cada entidad, en la transacción
    del llamante: crea las que faltan, retira las que sobran y no toca las iguales; si no hay
    nada que cambiar, no escribe nada. Nunca confirma."""
    expected = expected_cards(load_canon(uow.session, version_id))
    current = {
        ((card.entity_type, card.character_id, card.place_id), card.from_chapter): card
        for card in uow.session.scalars(select(CanonCard).where(CanonCard.version_id == version_id))
    }
    stale = [card for key, card in current.items() if expected.get(key) != card.text]
    for card in stale:
        uow.delete(card)
    if stale:
        # Una sustituta ocupa la clave de la retirada: la retirada sale antes de que entre.
        uow.session.flush()
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
        if (entity, from_chapter) not in current or current[(entity, from_chapter)] in stale
    ]
    for card in fresh:
        uow.add(card)
    store_vectors(uow, fresh, embedder)

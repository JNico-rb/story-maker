"""El recuperador híbrido de CanonCards para el capítulo *n* (`architecture.md` §6.3)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from story_maker.retrieval.dense import min_distances, novel_model
from story_maker.retrieval.embedding import EmbeddingModel, embed_texts
from story_maker.retrieval.lexical import bm25, candidates, words
from story_maker.store.models import CanonCard


@dataclass(frozen=True)
class RankedCard:
    """Una elegible con su rango en cada canal; sin rango léxico si no comparte ninguna palabra."""

    card: CanonCard
    lexical_rank: int | None
    lexical_score: float | None = None
    dense_rank: int | None = None


def eligible_cards(session: Session, version_id: int, chapter: int) -> list[CanonCard]:
    """Corte temporal: por entidad, la tarjeta de la versión de mayor `from_chapter` ≤ `chapter`."""
    cards = session.scalars(
        select(CanonCard)
        .where(CanonCard.version_id == version_id, CanonCard.from_chapter <= chapter)
        .order_by(CanonCard.from_chapter)
    )
    latest: dict[tuple[str, int | None, int | None], CanonCard] = {}
    for card in cards:
        latest[(card.entity_type, card.character_id, card.place_id)] = card
    return list(latest.values())


def rank_cards(
    session: Session,
    version_id: int,
    chapter: int,
    fragments: Sequence[str],
    embedder: EmbeddingModel,
) -> list[RankedCard]:
    """Todas las elegibles del capítulo `chapter`, en el orden de la fusión."""
    eligible = eligible_cards(session, version_id, chapter)
    query_words = {word for fragment in fragments for word in words(fragment)}
    lexical = candidates(session, query_words, [card.id for card in eligible])
    scores = bm25(query_words, {card.id: card.text for card in eligible}, lexical)
    by_score = sorted(scores, key=lambda card_id: -scores[card_id])
    lexical_ranks = {card_id: rank for rank, card_id in enumerate(by_score, start=1)}
    model = novel_model(session, version_id)
    query_vectors = embed_texts(embedder, model, fragments)
    distances = min_distances(session, model, [card.id for card in eligible], query_vectors)
    by_distance = sorted(distances, key=lambda card_id: distances[card_id])
    dense_ranks = {card_id: rank for rank, card_id in enumerate(by_distance, start=1)}
    return [
        RankedCard(card, lexical_ranks.get(card.id), scores.get(card.id), dense_ranks.get(card.id))
        for card in eligible
    ]


def retrieve(
    session: Session,
    version_id: int,
    chapter: int,
    fragments: Sequence[str],
    top_k: int,
    embedder: EmbeddingModel,
) -> list[CanonCard]:
    """Las `top_k` CanonCards de la versión para el capítulo `chapter` y esta consulta."""
    ranked = rank_cards(session, version_id, chapter, fragments, embedder)
    return [entry.card for entry in ranked[:top_k]]

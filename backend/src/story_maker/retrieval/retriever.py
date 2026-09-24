"""El recuperador híbrido de CanonCards para el capítulo *n* (`architecture.md` §6.3)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction

from sqlalchemy import select
from sqlalchemy.orm import Session

from story_maker.retrieval.dense import min_distances
from story_maker.retrieval.embedding import EmbeddingModel, embed_texts
from story_maker.retrieval.lexical import bm25, candidates, words
from story_maker.retrieval.vectors import novel_model
from story_maker.store.models import CanonCard

RRF_K = 60

# Orden del enumerado del tipo de entidad (`definitions.md` §12.4): primero decide el tipo.
ENTITY_TYPES = ("character", "place", "world")


def stable_key(card: CanonCard) -> tuple[int, int, int]:
    """Desempate estable: tipo de entidad, id de la entidad y `from_chapter`, ascendentes."""
    entity_id = card.character_id or card.place_id or 0
    return (ENTITY_TYPES.index(card.entity_type), entity_id, card.from_chapter)


@dataclass(frozen=True)
class RankedCard:
    """Una elegible con su rango en cada canal; sin rango léxico si no comparte ninguna palabra."""

    card: CanonCard
    lexical_rank: int | None
    lexical_score: float | None = None
    dense_rank: int | None = None

    @property
    def rrf(self) -> Fraction:
        """Σ 1 / (60 + rango) sobre los canales en que aparece; exacta, para que un empate sea
        un empate."""
        ranks = (rank for rank in (self.lexical_rank, self.dense_rank) if rank is not None)
        return sum((Fraction(1, RRF_K + rank) for rank in ranks), Fraction(0))


def fuse(entries: Iterable[RankedCard]) -> list[RankedCard]:
    """Las entradas por RRF descendente; los empates, por la clave estable."""
    return sorted(entries, key=lambda entry: (-entry.rrf, stable_key(entry.card)))


def channel_ranks(
    eligible: Sequence[CanonCard], measure: Mapping[int, float], *, higher_first: bool
) -> dict[int, int]:
    """Rangos consecutivos desde 1 de las tarjetas con `measure`; los empates, por la clave
    estable."""
    sign = -1 if higher_first else 1
    ranked = sorted(
        (card for card in eligible if card.id in measure),
        key=lambda card: (sign * measure[card.id], stable_key(card)),
    )
    return {card.id: rank for rank, card in enumerate(ranked, start=1)}


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
    lexical_ranks = channel_ranks(eligible, scores, higher_first=True)
    model = novel_model(session, version_id)
    query_vectors = embed_texts(embedder, model, fragments)
    distances = min_distances(session, model, [card.id for card in eligible], query_vectors)
    dense_ranks = channel_ranks(eligible, distances, higher_first=False)
    return fuse(
        RankedCard(card, lexical_ranks.get(card.id), scores.get(card.id), dense_ranks.get(card.id))
        for card in eligible
    )


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

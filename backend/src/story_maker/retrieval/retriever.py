"""El recuperador híbrido de CanonCards para el capítulo *n* (`architecture.md` §6.3)."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from story_maker.retrieval.embedding import EmbeddingModel
from story_maker.store.models import CanonCard


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


def retrieve(
    session: Session,
    version_id: int,
    chapter: int,
    fragments: Sequence[str],
    top_k: int,
    embedder: EmbeddingModel,
) -> list[CanonCard]:
    """Las `top_k` CanonCards de la versión para el capítulo `chapter` y esta consulta."""
    return eligible_cards(session, version_id, chapter)[:top_k]

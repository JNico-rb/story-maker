"""Vectores de las CanonCards por (huella, modelo), compartidos entre versiones y novelas
(`architecture.md` §6.3, §9.3)."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

from sqlalchemy import select

from story_maker.retrieval.embedding import EmbeddingModel, embed_texts
from story_maker.store.models import CanonCard, Embedding
from story_maker.store.session import UnitOfWork


def fingerprint(text: str) -> str:
    """La huella de una CanonCard: la de su texto."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def store_vectors(
    uow: UnitOfWork, model: str, cards: Sequence[CanonCard], embedder: EmbeddingModel
) -> None:
    """Deja con vector de `model` cada huella de `cards`, en la transacción de `uow`. El modelo
    solo incrusta, una vez, cada huella que aún no tiene vector; ninguno se toca después."""
    texts = {card.content_hash: card.text for card in cards}
    existing = set(
        uow.session.scalars(
            select(Embedding.content_hash).where(
                Embedding.model == model, Embedding.content_hash.in_(texts)
            )
        )
    )
    missing = sorted(set(texts) - existing)
    if not missing:
        return
    vectors = embed_texts(embedder, model, [texts[h] for h in missing])
    for content_hash, vector in zip(missing, vectors, strict=True):
        uow.add(Embedding(content_hash=content_hash, model=model, vector=vector))

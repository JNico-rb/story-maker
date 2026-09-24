"""Vectores de las CanonCards por (huella, modelo), compartidos entre versiones y novelas
(`architecture.md` §6.3, §9.3)."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from story_maker.retrieval.embedding import EmbeddingModel, embed_texts
from story_maker.store.models import CanonCard, Embedding, Novel, Version
from story_maker.store.session import UnitOfWork


def fingerprint(text: str) -> str:
    """La huella de una CanonCard: la de su texto."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def novel_model(session: Session, version_id: int) -> str:
    """El modelo de incrustación de la novela de la versión, fijo desde que se creó; la config
    no cuenta (`architecture.md` §6.3)."""
    return session.scalars(
        select(Novel.embedding_model)
        .join(Version, Version.novel_id == Novel.id)
        .where(Version.id == version_id)
    ).one()


def store_vectors(uow: UnitOfWork, cards: Sequence[CanonCard], embedder: EmbeddingModel) -> None:
    """Deja cada tarjeta de `cards` con vector del modelo de su novela, en la transacción de
    `uow`. El modelo solo incrusta, una vez, cada huella que aún no tiene vector suyo; ninguno se
    toca después."""
    models = {v: novel_model(uow.session, v) for v in {card.version_id for card in cards}}
    by_model: dict[str, dict[str, str]] = {}
    for card in cards:
        by_model.setdefault(models[card.version_id], {})[card.content_hash] = card.text
    for model, texts in sorted(by_model.items()):
        _store(uow, model, texts, embedder)


def _store(uow: UnitOfWork, model: str, texts: Mapping[str, str], embedder: EmbeddingModel) -> None:
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

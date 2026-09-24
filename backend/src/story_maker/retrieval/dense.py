"""Canal denso: distancia coseno con `sqlite-vec` entre cada tarjeta y cada fragmento de la
consulta, y cuenta la menor (`architecture.md` §6.3)."""

from __future__ import annotations

from collections.abc import Collection, Sequence

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

_DISTANCES = text(
    "SELECT c.id, vec_distance_cosine(e.vector, :query) FROM canon_cards c "
    "JOIN embeddings e ON e.content_hash = c.content_hash AND e.model = :model "
    "WHERE c.id IN :ids"
).bindparams(bindparam("ids", expanding=True))


def min_distances(
    session: Session, model: str, card_ids: Collection[int], query_vectors: Sequence[bytes]
) -> dict[int, float]:
    """Por tarjeta, la menor distancia coseno a un fragmento de la consulta."""
    best: dict[int, float] = {}
    if not card_ids:
        return best
    for query in query_vectors:
        rows = session.execute(_DISTANCES, {"query": query, "model": model, "ids": list(card_ids)})
        for card_id, distance in rows:
            best[card_id] = min(distance, best.get(card_id, distance))
    return best

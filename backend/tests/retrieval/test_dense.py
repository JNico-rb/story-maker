"""016-C14: el canal denso compara por fragmentos."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from story_maker.retrieval.fake import FixedVectors
from story_maker.retrieval.retriever import rank_cards

FAR = (0.0, 0.0, 0.0, 1.0)
OTHER = (1.0, 0.0, 0.0, 0.0)
NEAR_Y = (0.0, 1.0, 0.0, 0.0)
NEAR_Z = (0.0, 0.0, 1.0, 0.0)

PARAGRAPHS = ["Llueve sobre el pueblo.", "Nadie sale de casa.", "Suena la sirena del barco."]
BEATS = ["Marta abre la tienda.", "Marta encuentra la carta.", "Marta cierra la tienda."]

CARD_TEXTS = {
    "otra": "Rosa, la vecina.",
    "y": "La carta de la abuela.",
    "z": "El barco del puerto.",
}
VECTORS = {
    CARD_TEXTS["otra"]: OTHER,
    CARD_TEXTS["y"]: NEAR_Y,
    CARD_TEXTS["z"]: NEAR_Z,
    PARAGRAPHS[0]: FAR,
    PARAGRAPHS[1]: FAR,
    PARAGRAPHS[2]: NEAR_Z,
    BEATS[0]: FAR,
    BEATS[1]: NEAR_Y,
    BEATS[2]: FAR,
}


def dense_ranks(
    session_factory: sessionmaker[Session], version: int, fragments: list[str], vectors: Any
) -> dict[int, int | None]:
    with session_factory() as session:
        ranked = rank_cards(session, version, 1, fragments, vectors)
        return {entry.card.id: entry.dense_rank for entry in ranked}


def test_a_card_near_a_single_fragment_leads_the_dense_channel(
    canon: Any, session_factory: sessionmaker[Session]
) -> None:
    vectors = FixedVectors(VECTORS, default=OTHER)
    version = canon.version()
    cards = {
        "otra": canon.card(
            version,
            CARD_TEXTS["otra"],
            character=canon.character(version, "Rosa"),
            embedder=vectors,
        ),
        "y": canon.card(
            version, CARD_TEXTS["y"], place=canon.place(version, "la tienda"), embedder=vectors
        ),
        "z": canon.card(version, CARD_TEXTS["z"], embedder=vectors),
    }

    editor = dense_ranks(session_factory, version, PARAGRAPHS, vectors)
    writer = dense_ranks(session_factory, version, BEATS, vectors)

    assert editor[cards["z"]] == 1
    assert writer[cards["y"]] == 1
    assert sorted(rank for rank in editor.values() if rank is not None) == [1, 2, 3]
    assert sorted(rank for rank in writer.values() if rank is not None) == [1, 2, 3]

"""016-C11 a 016-C13: el canal léxico."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker

from story_maker.retrieval.fake import FixedVectors
from story_maker.retrieval.retriever import rank_cards


def lexical_ranks(
    session_factory: sessionmaker[Session],
    version: int,
    query: str,
    embedder: FixedVectors,
    chapter: int = 1,
) -> dict[int, int]:
    """Tarjeta → rango léxico, solo de las que están en el ranking léxico."""
    with session_factory() as session:
        ranked = rank_cards(session, version, chapter, [query], embedder)
        return {e.card.id: e.lexical_rank for e in ranked if e.lexical_rank is not None}


@pytest.fixture
def words_version(canon: Any) -> tuple[int, dict[str, int]]:
    version = canon.version()
    cards = {
        "toby": canon.card(version, "Toby duerme.", character=canon.character(version, "Toby")),
        "arbol": canon.card(version, "Un árbol viejo.", place=canon.place(version, "el huerto")),
        "examen": canon.card(version, "El examen final.", place=canon.place(version, "el aula")),
        "otra": canon.card(version, "Nada que ver.", character=canon.character(version, "Nia")),
    }
    return version, cards


@pytest.mark.parametrize(("query", "matched"), [("TÓBY", "toby"), ("arbol", "arbol")])
def test_the_lexical_channel_ignores_case_and_diacritics(
    session_factory: sessionmaker[Session],
    words_version: tuple[int, dict[str, int]],
    embedder: FixedVectors,
    query: str,
    matched: str,
) -> None:
    version, cards = words_version

    assert set(lexical_ranks(session_factory, version, query, embedder)) == {cards[matched]}


def test_the_lexical_channel_compares_whole_words_not_prefixes(
    session_factory: sessionmaker[Session],
    words_version: tuple[int, dict[str, int]],
    embedder: FixedVectors,
) -> None:
    version, _cards = words_version

    assert lexical_ranks(session_factory, version, "ex", embedder) == {}


def test_a_card_is_in_the_lexical_ranking_if_and_only_if_it_shares_a_word(
    session_factory: sessionmaker[Session],
    words_version: tuple[int, dict[str, int]],
    embedder: FixedVectors,
) -> None:
    version, cards = words_version

    ranks = lexical_ranks(session_factory, version, "toby bajo el árbol", embedder)

    assert set(ranks) == {cards["toby"], cards["arbol"], cards["examen"]}

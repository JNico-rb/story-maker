"""016-C12: BM25 con las estadísticas de la versión en el capítulo *n*."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker

from story_maker.retrieval.fake import FixedVectors
from story_maker.retrieval.retriever import rank_cards
from story_maker.store.models import CanonCard

QUERY = "faro tormenta"


@pytest.fixture
def storm(canon: Any) -> dict[str, Any]:
    """Cinco elegibles en el capítulo 5: «faro» en una y «tormenta» en cuatro."""
    version = canon.version()
    storm_cards = []
    for index, name in enumerate(("Rosa", "Julio", "Aurora", "Bruno")):
        character = canon.character(version, name)
        storm_cards.append(
            canon.card(
                version,
                f"{name} recuerda la tormenta del cabo.",
                character=character,
                from_chapter=2 if index == 0 else 1,
            )
        )
    lighthouse = canon.card(
        version, "El faro del cabo vigila.", place=canon.place(version, "el faro"), from_chapter=5
    )
    return {"version": version, "lighthouse": lighthouse, "storm": storm_cards}


def lexical_ranking(
    session_factory: sessionmaker[Session], version: int, embedder: FixedVectors
) -> list[tuple[int, int | None, float | None]]:
    with session_factory() as session:
        ranked = rank_cards(session, version, 5, [QUERY], embedder)
        lexical = [e for e in ranked if e.lexical_rank is not None]
        lexical.sort(key=lambda e: e.lexical_rank or 0)
        return [(e.card.id, e.lexical_rank, e.lexical_score) for e in lexical]


def test_a_rare_word_ranks_its_card_above_those_with_only_a_common_word(
    session_factory: sessionmaker[Session], storm: dict[str, Any], embedder: FixedVectors
) -> None:
    ranking = lexical_ranking(session_factory, storm["version"], embedder)

    assert ranking[0][0] == storm["lighthouse"]
    assert {card for card, _, _ in ranking[1:]} == set(storm["storm"])


def fifty_lighthouses(canon: Any, version: int) -> None:
    for index in range(50):
        character = canon.character(version, f"Farero {index}")
        canon.card(version, f"El faro {index} y otro faro.", character=character)


def add_lighthouses_in_another_novel(canon: Any, storm: dict[str, Any]) -> None:
    fifty_lighthouses(canon, canon.version())


def add_lighthouses_in_another_version(canon: Any, storm: dict[str, Any]) -> None:
    fifty_lighthouses(canon, canon.other_version(storm["version"]))


def add_a_future_card(canon: Any, storm: dict[str, Any]) -> None:
    version = storm["version"]
    place = canon.place(version, "el puerto nuevo")
    canon.card(version, "El faro faro faro del puerto nuevo.", place=place, from_chapter=8)


def add_a_superseded_card(canon: Any, storm: dict[str, Any]) -> None:
    """Una tarjeta anterior de la entidad de la primera tarjeta con «tormenta» (desde el 2)."""
    version = storm["version"]
    with canon.session_factory() as session:
        successor = session.get(CanonCard, storm["storm"][0])
        assert successor is not None
        character = successor.character_id
    canon.card(version, "Faro, faro, faro y más faro.", character=character, from_chapter=1)


@pytest.mark.parametrize(
    "addition",
    [
        add_lighthouses_in_another_novel,
        add_lighthouses_in_another_version,
        add_a_future_card,
        add_a_superseded_card,
    ],
)
def test_the_lexical_ranking_and_scores_use_only_the_eligible_cards_of_the_version(
    canon: Any,
    session_factory: sessionmaker[Session],
    storm: dict[str, Any],
    embedder: FixedVectors,
    addition: Callable[[Any, dict[str, Any]], None],
) -> None:
    before = lexical_ranking(session_factory, storm["version"], embedder)
    assert len(before) == 5
    assert all(score is not None for _, _, score in before)

    addition(canon, storm)

    assert lexical_ranking(session_factory, storm["version"], embedder) == before

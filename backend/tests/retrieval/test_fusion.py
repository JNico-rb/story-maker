"""016-C15 y 016-C16: fusión RRF con k = 60 y desempate estable."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from story_maker.retrieval.fake import FixedVectors
from story_maker.retrieval.retriever import RankedCard, fuse, rank_cards
from story_maker.store.models import CanonCard


def character_card(character_id: int, from_chapter: int = 1) -> CanonCard:
    return CanonCard(
        id=character_id,
        entity_type="character",
        character_id=character_id,
        from_chapter=from_chapter,
        text="",
        content_hash="",
    )


def test_rrf_adds_one_over_sixty_plus_the_rank_of_each_channel() -> None:
    a = RankedCard(character_card(1), lexical_rank=1, dense_rank=3)
    b = RankedCard(character_card(2), lexical_rank=2, dense_rank=1)
    c = RankedCard(character_card(3), lexical_rank=None, dense_rank=2)
    d = RankedCard(character_card(4), lexical_rank=None, dense_rank=4)

    fused = fuse([a, b, c, d])

    assert [entry.card.id for entry in fused] == [2, 1, 3, 4]
    assert [entry.rrf for entry in fused] == [
        Fraction(1, 62) + Fraction(1, 61),
        Fraction(1, 61) + Fraction(1, 63),
        Fraction(1, 62),
        Fraction(1, 64),
    ]


def place_card(place_id: int, from_chapter: int = 1) -> CanonCard:
    return CanonCard(
        id=100 + place_id,
        entity_type="place",
        place_id=place_id,
        from_chapter=from_chapter,
        text="",
        content_hash="",
    )


def test_an_rrf_tie_puts_characters_before_places_whatever_their_ids() -> None:
    place_7 = RankedCard(place_card(7), lexical_rank=1, dense_rank=2)
    character_9 = RankedCard(character_card(9), lexical_rank=2, dense_rank=1)

    fused = fuse([place_7, character_9])

    assert place_7.rrf == character_9.rrf
    assert [entry.card for entry in fused] == [character_9.card, place_7.card]


def test_an_rrf_tie_between_two_characters_goes_by_entity_id() -> None:
    character_5 = RankedCard(character_card(5), lexical_rank=1, dense_rank=2)
    character_3 = RankedCard(character_card(3), lexical_rank=2, dense_rank=1)

    fused = fuse([character_5, character_3])

    assert [entry.card.character_id for entry in fused] == [3, 5]


def test_ties_inside_a_channel_get_consecutive_ranks_by_the_stable_key_every_time(
    canon: Any, session_factory: sessionmaker[Session], embedder: FixedVectors
) -> None:
    version = canon.version()
    first = canon.character(version, "Toby")
    second = canon.character(version, "Nala")
    second_card = canon.card(version, "Nala ladra.", character=second)
    first_card = canon.card(version, "Toby ladra.", character=first)

    def ranking() -> list[tuple[int, int | None, float | None, int | None]]:
        with session_factory() as session:
            ranked = rank_cards(session, version, 1, ["ladra"], embedder)
            return [(e.card.id, e.lexical_rank, e.lexical_score, e.dense_rank) for e in ranked]

    once, twice = ranking(), ranking()

    by_card = {card: (lexical, score, dense) for card, lexical, score, dense in once}
    assert by_card[first_card][1] == by_card[second_card][1]
    assert (by_card[first_card][0], by_card[second_card][0]) == (1, 2)
    assert (by_card[first_card][2], by_card[second_card][2]) == (1, 2)
    assert [card for card, _, _, _ in once] == [first_card, second_card]
    assert once == twice

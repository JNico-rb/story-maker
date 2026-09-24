"""016-C15 y 016-C16: fusión RRF con k = 60 y desempate estable."""

from __future__ import annotations

from fractions import Fraction

from story_maker.retrieval.retriever import RankedCard, fuse
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

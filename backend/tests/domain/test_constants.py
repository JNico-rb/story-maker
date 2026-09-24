"""Constantes del dominio propias del plan y del outline (`definitions.md` §11.2; 010)."""

from __future__ import annotations

from story_maker.domain.constants import MAX_BEATS, MAX_CONSEQUENCES, MIN_BEATS, MIN_CONSEQUENCES


def test_a_world_has_from_two_to_four_consequences() -> None:
    assert (MIN_CONSEQUENCES, MAX_CONSEQUENCES) == (2, 4)


def test_a_chapter_has_from_three_to_six_beats() -> None:
    assert (MIN_BEATS, MAX_BEATS) == (3, 6)

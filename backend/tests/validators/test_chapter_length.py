"""`longitud-capitulo` en sus límites y qué es una palabra (011-C11)."""

from __future__ import annotations

import pytest

from story_maker.validators.chapter_length import LENGTH, check_chapter_length, count_words


def text_of(words: int) -> str:
    return " ".join(["palabra"] * words)


def test_a_word_is_a_run_without_spaces_with_a_letter_or_a_digit() -> None:
    assert count_words("—Hola —dijo.") == 2
    assert count_words("Y entonces — nada … más") == 4
    assert count_words("Costó 1.250 euros") == 3
    assert count_words("uno\n\ndos\ttres") == 3


@pytest.mark.parametrize(
    ("words", "passes"), [(999, False), (1000, True), (1500, True), (1501, False)]
)
def test_the_length_passes_from_1000_to_1500_words(words: int, passes: bool) -> None:
    check = check_chapter_length(text_of(words))

    assert check.validator == LENGTH
    assert check.passed is passes
    assert str(words) in check.comment


def test_a_blocking_defect_names_the_validator_the_words_counted_and_the_range() -> None:
    check = check_chapter_length(text_of(999))

    assert len(check.defects) == 1
    defect = check.defects[0]
    assert defect.validator == LENGTH
    assert defect.blocking is True
    assert "999" in defect.message
    assert "1.000" in defect.message
    assert "1.500" in defect.message


def test_a_passing_length_has_no_defects() -> None:
    assert check_chapter_length(text_of(1250)).defects == ()

"""`revision-visual`: la comparación entre lo observado y lo esperado (017-C04 a 017-C09,
017-C13, 017-I1, 017-I4), sin base de datos ni sesión."""

from __future__ import annotations

from typing import Any

import pytest
from tests.pipeline.gate.visual import EXPECTED, chapter_text, faithful, first_sentence

from story_maker.validators.visual_review import (
    PARTS,
    VisualReviewSubmission,
    VisualVerdict,
    compare,
    sentence_in,
    texts_match,
)


def verdict_of(delivery: dict[str, Any]) -> VisualVerdict:
    return compare(EXPECTED, VisualReviewSubmission.model_validate(delivery))


# --- 017-C04 -------------------------------------------------------------------------------------


def test_a_review_that_observes_exactly_the_expected_passes_in_the_four_parts() -> None:
    verdict = verdict_of(faithful())

    assert verdict.passed
    assert verdict.parts == tuple((part, True) for part in PARTS)
    assert verdict.defects == ()


# --- 017-C05 -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("observed", "expected", "match"),
    [
        ("MARTA", "Marta", True),
        ("Para  Marta,\ncon cariño", "Para Marta, con cariño", True),
        ("Martha", "Marta", False),
        ("Márta", "Marta", False),
        ("Para Marta con cariño", "Para Marta, con cariño", False),
    ],
)
def test_two_texts_match_ignoring_spaces_and_case_but_never_letters_accents_or_signs(
    observed: str, expected: str, match: bool
) -> None:
    assert texts_match(observed, expected) is match


@pytest.mark.parametrize(
    ("observed", "match"),
    [(first_sentence(3), True), (first_sentence(4), False), ("", False)],
)
def test_a_first_sentence_matches_only_if_it_is_in_the_text_of_its_chapter(
    observed: str, match: bool
) -> None:
    assert sentence_in(observed, chapter_text(3)) is match

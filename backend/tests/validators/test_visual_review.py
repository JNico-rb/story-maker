"""`revision-visual`: la comparación entre lo observado y lo esperado (017-C04 a 017-C09,
017-C13, 017-I1, 017-I4), sin base de datos ni sesión."""

from __future__ import annotations

from typing import Any

from tests.pipeline.gate.visual import EXPECTED, faithful

from story_maker.validators.visual_review import (
    PARTS,
    VisualReviewSubmission,
    VisualVerdict,
    compare,
)


def verdict_of(delivery: dict[str, Any]) -> VisualVerdict:
    return compare(EXPECTED, VisualReviewSubmission.model_validate(delivery))


# --- 017-C04 -------------------------------------------------------------------------------------


def test_a_review_that_observes_exactly_the_expected_passes_in_the_four_parts() -> None:
    verdict = verdict_of(faithful())

    assert verdict.passed
    assert verdict.parts == tuple((part, True) for part in PARTS)
    assert verdict.defects == ()

"""Precedencia entre resultados dentro de una pasada (012-C17)."""

from __future__ import annotations

from story_maker.formal.defects import Defect
from story_maker.pipeline.gate.precedence import gate_precedence

LEAN = "cronologia-lean"
JUDGE = "juez-novela"


def _blocking(validator: str, chapter: int) -> Defect:
    return Defect(validator, None, True, chapter, "defecto")


# --- Tabla de 012-C17 ------------------------------------------------------------------------


def test_witness_without_chapter_beats_a_blocking_judge_defect() -> None:
    verdict = gate_precedence(
        unattributable_reason="unattributable_defect",
        defects=(_blocking(JUDGE, 4),),
    )

    assert verdict.outcome == "fail"
    assert verdict.reason == "unattributable_defect"


def test_an_unreachable_verifier_beats_a_blocking_judge_defect_and_nothing_is_rewritten() -> None:
    verdict = gate_precedence(
        interruption_reason="verifier_unreachable",
        defects=(_blocking(JUDGE, 4),),
    )

    assert verdict.outcome == "interrupted"
    assert verdict.reason == "verifier_unreachable"
    assert verdict.chapters_to_rewrite == ()


def test_a_witness_in_6_and_a_blocking_judge_defect_in_4_rewrite_both_in_the_same_cycle() -> None:
    verdict = gate_precedence(defects=(_blocking(LEAN, 6), _blocking(JUDGE, 4)))

    assert verdict.outcome == "rewrite"
    assert verdict.chapters_to_rewrite == (4, 6)


def test_a_witness_in_6_with_no_valid_judge_delivery_rewrites_only_6() -> None:
    verdict = gate_precedence(defects=(_blocking(LEAN, 6),), judge_no_valid_delivery=True)

    assert verdict.outcome == "rewrite"
    assert verdict.chapters_to_rewrite == (6,)


def test_a_passed_verifier_with_a_provider_error_from_the_judge_is_interrupted() -> None:
    verdict = gate_precedence(interruption_reason="provider_error", defects=())

    assert verdict.outcome == "interrupted"
    assert verdict.reason == "provider_error"


def test_a_chronology_file_error_beats_a_provider_error_from_the_judge() -> None:
    verdict = gate_precedence(
        unattributable_reason="internal_error", interruption_reason="provider_error"
    )

    assert verdict.outcome == "fail"
    assert verdict.reason == "internal_error"


# --- Otros bordes de la precedencia ------------------------------------------------------------


def test_no_defects_no_interruption_lets_the_pass_continue() -> None:
    verdict = gate_precedence()

    assert verdict.outcome == "continue"
    assert verdict.chapters_to_rewrite == ()


def test_no_valid_judge_delivery_with_no_lean_defect_still_fails_the_pass_if_it_rewrites() -> None:
    verdict = gate_precedence(judge_no_valid_delivery=True, cycles_remaining=True)

    assert verdict.outcome == "rewrite"
    assert verdict.chapters_to_rewrite == ()


def test_exhausted_cycles_with_attributable_defects_fails_with_retries_exhausted() -> None:
    verdict = gate_precedence(defects=(_blocking(JUDGE, 4),), cycles_remaining=False)

    assert verdict.outcome == "fail"
    assert verdict.reason == "retries_exhausted"


def test_non_blocking_defects_alone_do_not_trigger_a_rewrite() -> None:
    non_blocking = Defect(JUDGE, "ritmo", False, 9, "defecto no bloqueante")

    verdict = gate_precedence(defects=(non_blocking,))

    assert verdict.outcome == "continue"

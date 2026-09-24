"""`juez-novela`: schema de `submit_evaluation`, ventana de la sesión y agregación del veredicto
(012-C13, 012-C14, 012-C15, 012-C16, 012-I5)."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from story_maker.domain.trope_catalog import TROPE_CATALOG
from story_maker.pipeline.planning.brief_view import BriefView, RecipientView
from story_maker.store.story_bible import (
    CharacterEntry,
    Chronology,
    FactEntry,
    PlaceEntry,
    StoryBible,
)
from story_maker.validators.judge import (
    VALIDATOR,
    JudgeChapter,
    JudgeEvaluation,
    build_judge_window,
    judge_result,
    submit_evaluation_tool,
)

THRESHOLDS = {
    "continuidad": 3,
    "coherencia-personajes": 3,
    "arco-y-final": 3,
    "ritmo": 3,
    "tono": 3,
    "personalizacion-natural": 3,
    "no-cliche": 3,
}


def _criterion(score: int, chapters: tuple[int, ...] = (1,), justification: str = "justo") -> dict:
    return {"score": score, "justification": justification, "chapters": list(chapters)}


def _submission(**overrides: dict) -> dict:
    base = {
        "continuidad": _criterion(4),
        "coherencia-personajes": _criterion(4),
        "arco-y-final": _criterion(4),
        "ritmo": _criterion(4),
        "tono": _criterion(4),
        "personalizacion-natural": _criterion(4),
        "no-cliche": _criterion(4),
    }
    base.update(overrides)
    return base


# --- 012-C15 · schema de submit_evaluation ------------------------------------------------------


def test_a_valid_submission_parses() -> None:
    evaluation = JudgeEvaluation.model_validate(_submission())

    assert evaluation.continuidad.score == 4


def test_a_missing_criterion_is_rejected() -> None:
    raw = _submission()
    del raw["ritmo"]

    with pytest.raises(ValidationError):
        JudgeEvaluation.model_validate(raw)


def test_an_unknown_extra_criterion_is_rejected() -> None:
    raw = _submission(**{"criterio-inventado": _criterion(4)})

    with pytest.raises(ValidationError):
        JudgeEvaluation.model_validate(raw)


def test_a_score_out_of_range_is_rejected() -> None:
    raw = _submission(continuidad=_criterion(6))

    with pytest.raises(ValidationError):
        JudgeEvaluation.model_validate(raw)


def test_an_empty_justification_is_rejected() -> None:
    raw = _submission(continuidad=_criterion(4, justification=""))

    with pytest.raises(ValidationError):
        JudgeEvaluation.model_validate(raw)


def test_a_criterion_citing_no_chapter_is_rejected() -> None:
    raw = _submission(continuidad=_criterion(4, chapters=()))

    with pytest.raises(ValidationError):
        JudgeEvaluation.model_validate(raw)


def test_a_criterion_citing_a_chapter_out_of_range_is_rejected() -> None:
    raw = _submission(continuidad=_criterion(4, chapters=(11,)))

    with pytest.raises(ValidationError):
        JudgeEvaluation.model_validate(raw)


def test_a_criterion_citing_a_repeated_chapter_is_rejected() -> None:
    raw = _submission(continuidad=_criterion(4, chapters=(3, 3)))

    with pytest.raises(ValidationError):
        JudgeEvaluation.model_validate(raw)


def test_submit_evaluation_is_the_only_tool() -> None:
    tool = submit_evaluation_tool()

    assert tool.name == "submit_evaluation"
    assert tool.model is JudgeEvaluation


# --- 012-C13 · un bloqueante bajo su umbral se atribuye a los capítulos que cita ----------------


def test_a_blocking_criterion_below_threshold_attributes_blocking_defects_and_fails() -> None:
    raw = _submission(
        continuidad=_criterion(2, chapters=(4, 7)),
        ritmo=_criterion(2, chapters=(4, 9)),
    )
    evaluation = JudgeEvaluation.model_validate(raw)

    verdict = judge_result(evaluation, THRESHOLDS)

    assert not verdict.passed
    assert verdict.score == 0.0
    continuidad_defects = [d for d in verdict.defects if d.criterion == "continuidad"]
    ritmo_defects = [d for d in verdict.defects if d.criterion == "ritmo"]
    assert {d.chapter for d in continuidad_defects} == {4, 7}
    assert all(d.blocking for d in continuidad_defects)
    assert {d.chapter for d in ritmo_defects} == {4, 9}
    assert all(not d.blocking for d in ritmo_defects)
    assert all(d.validator == VALIDATOR for d in verdict.defects)


def test_a_blocking_criterion_at_the_threshold_passes() -> None:
    raw = _submission(continuidad=_criterion(3, chapters=(4, 7)))
    evaluation = JudgeEvaluation.model_validate(raw)

    verdict = judge_result(evaluation, THRESHOLDS)

    assert verdict.passed
    assert not any(d.criterion == "continuidad" for d in verdict.defects)


# --- 012-C14 · ningún criterio compensa a otro --------------------------------------------------


def test_one_low_blocking_criterion_fails_even_with_the_rest_high() -> None:
    raw = _submission(**{"arco-y-final": _criterion(2, chapters=(3, 6))})
    evaluation = JudgeEvaluation.model_validate(raw)

    verdict = judge_result(evaluation, THRESHOLDS)

    assert not verdict.passed
    assert {d.chapter for d in verdict.defects} == {3, 6}
    assert all(d.criterion == "arco-y-final" and d.blocking for d in verdict.defects)


def test_low_non_blocking_criteria_do_not_fail_the_stage_but_are_reported() -> None:
    raw = _submission(
        **{
            "personalizacion-natural": _criterion(1, chapters=(2,)),
            "tono": _criterion(1, chapters=(2,)),
            "no-cliche": _criterion(1, chapters=(2,)),
        }
    )
    evaluation = JudgeEvaluation.model_validate(raw)

    verdict = judge_result(evaluation, THRESHOLDS)

    assert verdict.passed
    assert verdict.score == 1.0
    assert len(verdict.defects) == 3
    assert all(not d.blocking for d in verdict.defects)


# --- 012-I5 · el veredicto solo con campos estructurados ----------------------------------------


def test_the_justification_text_naming_another_chapter_does_not_change_the_attribution() -> None:
    raw = _submission(
        continuidad=_criterion(
            2, chapters=(4,), justification="el problema real está en el capítulo 8"
        )
    )
    evaluation = JudgeEvaluation.model_validate(raw)

    verdict = judge_result(evaluation, THRESHOLDS)

    assert {d.chapter for d in verdict.defects} == {4}


def test_no_average_is_taken_across_criteria() -> None:
    # Un bloqueante en 1 y los otros dos bloqueantes en 5 no compensan a un 3 de umbral: no hay
    # media (012-C14, 012-I5): el fallo depende solo de la puntuación de cada criterio, no de un
    # agregado numérico.
    raw = _submission(
        continuidad=_criterion(1, chapters=(1,)),
        **{
            "coherencia-personajes": _criterion(5, chapters=(1,)),
            "arco-y-final": _criterion(5, chapters=(1,)),
        },
    )
    evaluation = JudgeEvaluation.model_validate(raw)

    verdict = judge_result(evaluation, THRESHOLDS)

    assert not verdict.passed


# --- 012-C16 · lo que recibe la sesión del juez -------------------------------------------------


def _story_bible() -> StoryBible:
    return StoryBible(
        version_id=1,
        present_year=2026,
        world=None,
        characters=(CharacterEntry(1, "recipient", "person", "Toby", None, "brief"),),
        places=(PlaceEntry(2, "el faro", "un faro viejo", "brief"),),
        facts=(
            FactEntry(
                1, "character", 1, None, "favorite_color", "azul", "brief", False, None, False, (1,)
            ),
        ),
        chronology=Chronology(events=(), births=(), novum_date=None),
    )


def _brief() -> BriefView:
    return BriefView(
        recipient=RecipientView("Toby", 9),
        genre="ciencia ficción",
        tone="cálido",
        plot_wishes=("un dron amigable",),
        dedication="para Toby, con secretos que aquí no van",
    )


def test_the_window_carries_the_novel_the_compact_bible_the_rubric_and_the_catalog() -> None:
    chapters = (JudgeChapter(1, "El comienzo", "Había una vez..."),)

    message = build_judge_window("Una novela", chapters, _story_bible(), TROPE_CATALOG, _brief())
    payload = json.loads(message)

    assert payload["title"] == "Una novela"
    assert payload["chapters"] == [
        {"number": 1, "title": "El comienzo", "text": "Había una vez..."}
    ]
    assert payload["story_bible"]["characters"] == [
        {"name": "Toby", "facts": [{"attribute": "favorite_color", "value": "azul"}]}
    ]
    assert payload["story_bible"]["places"] == [{"name": "el faro", "facts": []}]
    assert len(payload["rubric"]) == 7
    assert len(payload["trope_catalog"]) == len(TROPE_CATALOG)
    assert payload["brief"] == {
        "tone": "cálido",
        "genre": "ciencia ficción",
        "plot_wishes": ["un dron amigable"],
    }


def test_the_window_never_carries_the_dedication_or_anything_outside_its_allowed_keys() -> None:
    chapters = (JudgeChapter(1, "El comienzo", "Había una vez..."),)

    message = build_judge_window("Una novela", chapters, _story_bible(), TROPE_CATALOG, _brief())

    assert "secretos" not in message
    payload = json.loads(message)
    assert set(payload.keys()) == {
        "title",
        "chapters",
        "story_bible",
        "rubric",
        "trope_catalog",
        "brief",
    }

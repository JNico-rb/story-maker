"""Texto sin palabras: ningún linter avisa, ni el de narrador en primera persona (018-C17)."""

from __future__ import annotations

import pytest

from story_maker.lint.ai_style import lint_ai_style
from story_maker.lint.consistency import StyleSheetInput, lint_consistency
from story_maker.lint.readability import ReadabilityTarget, lint_readability
from story_maker.lint.repetition import lint_repetition

_TARGET = ReadabilityTarget(age_band="adult", max_sentence_length=20, min_fernandez_huerta=0)


@pytest.mark.parametrize("text", ["", "...", "¡¿?!"])
def test_repeticion_sin_palabras_no_avisa_y_su_metrica_es_cero(text: str) -> None:
    result = lint_repetition(text)

    assert result.passed is True
    assert result.metric == 0
    assert result.defects == ()


@pytest.mark.parametrize("text", ["", "...", "¡¿?!"])
def test_legibilidad_sin_palabras_no_avisa_y_no_tiene_metrica(text: str) -> None:
    result = lint_readability(text, _TARGET)

    assert result.passed is True
    assert result.metric is None
    assert result.defects == ()


@pytest.mark.parametrize("text", ["", "...", "¡¿?!"])
def test_estilo_ia_sin_palabras_no_avisa_y_no_tiene_metrica(text: str) -> None:
    result = lint_ai_style(text)

    assert result.passed is True
    assert result.metric is None
    assert result.defects == ()


@pytest.mark.parametrize("text", ["", "...", "¡¿?!"])
@pytest.mark.parametrize("narrator", ["third_person", "first_person"])
def test_consistencia_sin_palabras_no_avisa_ni_para_primera_persona(
    text: str, narrator: str
) -> None:
    style_sheet = StyleSheetInput(narrator=narrator, default_treatment="tu")
    result = lint_consistency(text, style_sheet)

    assert result.passed is True
    assert result.metric == 0
    assert result.defects == ()

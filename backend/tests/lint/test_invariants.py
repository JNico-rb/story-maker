"""Invariantes de los cuatro linters: avisos no bloqueantes y determinismo
(018-I1, 018-I2)."""

from __future__ import annotations

import dataclasses

from hypothesis import given
from hypothesis import strategies as st

from story_maker.lint.ai_style import lint_ai_style
from story_maker.lint.consistency import StyleSheetInput, lint_consistency
from story_maker.lint.readability import ReadabilityTarget, lint_readability
from story_maker.lint.repetition import lint_repetition
from story_maker.lint.types import Defect

_TARGET = ReadabilityTarget(age_band="children", max_sentence_length=1, min_fernandez_huerta=1000)
_THIRD_PERSON = StyleSheetInput(narrator="third_person", default_treatment="tu")

# Un texto que dispara los cuatro linters a la vez.
_TRIGGERING_TEXT = (
    "Yo caminaba despacio y de repente vi la ventana, la ventana y la ventana "
    "otra vez, rápidamente asustada por un escalofrío le recorrió la espalda."
)


def test_defecto_no_tiene_ni_bloqueante_ni_criterio_de_rubrica() -> None:
    """`Defect` no declara ni bloqueante ni criterio: todo aviso de un linter es, por
    construcción, un `Defecto` no bloqueante y sin criterio de rúbrica (018-I1)."""
    field_names = {field.name for field in dataclasses.fields(Defect)}
    assert field_names == {"message", "paragraph"}


def test_cada_aviso_nombra_lo_detectado_con_un_mensaje_no_vacio() -> None:
    """Todo aviso trae un mensaje no vacío, y su párrafo cuando el hallazgo es de uno
    concreto: `linter-repeticion` siempre lo tiene, y `linter-consistencia` también,
    salvo el caso de capítulo entero de C13 (018-I1)."""
    results = [
        lint_repetition(_TRIGGERING_TEXT),
        lint_readability(_TRIGGERING_TEXT, _TARGET),
        lint_ai_style(_TRIGGERING_TEXT),
        lint_consistency(_TRIGGERING_TEXT, _THIRD_PERSON),
    ]
    all_defects = [defect for result in results for defect in result.defects]
    assert all_defects, "el texto de disparo debe producir al menos un aviso"
    for defect in all_defects:
        assert defect.message
        assert defect.paragraph is None or defect.paragraph >= 1

    for defect in lint_repetition(_TRIGGERING_TEXT).defects:
        assert defect.paragraph is not None

    chapter_wide_message = (
        "el capítulo no tiene marcas de primera persona en la narración; "
        "la StyleSheet pide primera persona"
    )
    for defect in lint_consistency(_TRIGGERING_TEXT, _THIRD_PERSON).defects:
        assert defect.paragraph is not None or defect.message == chapter_wide_message


@given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=0x2026), max_size=200))
def test_linter_repeticion_es_determinista(text: str) -> None:
    first = lint_repetition(text)
    second = lint_repetition(text)
    assert first.passed == second.passed
    assert first.metric == second.metric
    assert first.defects == second.defects


@given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=0x2026), max_size=200))
def test_linter_estilo_ia_es_determinista(text: str) -> None:
    first = lint_ai_style(text)
    second = lint_ai_style(text)
    assert first.passed == second.passed
    assert first.metric == second.metric
    assert first.defects == second.defects


@given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=0x2026), max_size=200))
def test_linter_consistencia_es_determinista(text: str) -> None:
    first = lint_consistency(text, _THIRD_PERSON)
    second = lint_consistency(text, _THIRD_PERSON)
    assert first.passed == second.passed
    assert first.metric == second.metric
    assert first.defects == second.defects


@given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=0x2026), max_size=200))
def test_linter_legibilidad_es_determinista(text: str) -> None:
    first = lint_readability(text, _TARGET)
    second = lint_readability(text, _TARGET)
    assert first.passed == second.passed
    assert first.metric == second.metric
    assert first.defects == second.defects

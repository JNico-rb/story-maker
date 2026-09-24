"""`linter-estilo-ia`: adverbios en -mente y palabras en -mente que no lo son
(018-C9, 018-C10)."""

from __future__ import annotations

from story_maker.lint.ai_style import lint_ai_style

_VALIDATOR = "linter-estilo-ia"


def test_la_densidad_en_su_umbral_no_dispara() -> None:
    text = " ".join(["gato"] * 497 + ["rápidamente"] * 3)
    result = lint_ai_style(text)

    assert result.validator == _VALIDATOR
    assert result.passed is True
    assert result.metric == 6.0
    assert result.defects == ()


def test_la_densidad_por_encima_del_umbral_dispara() -> None:
    text = " ".join(["gato"] * 496 + ["rápidamente"] * 4)
    result = lint_ai_style(text)

    assert result.passed is False
    assert result.metric == 8.0
    assert len(result.defects) == 1
    assert result.defects[0].message == ("8,00 adverbios en -mente por 1.000 palabras; umbral: 6")


def test_las_palabras_en_mente_de_la_lista_cerrada_no_son_adverbios() -> None:
    text = "mente demente clemente vehemente comente aumente lamente"
    result = lint_ai_style(text)

    assert result.passed is True
    assert result.metric == 0.0


def test_las_palabras_en_mente_fuera_de_la_lista_si_son_adverbios() -> None:
    text = "rápidamente suavemente fácilmente"
    result = lint_ai_style(text)

    assert result.metric == 1000.0

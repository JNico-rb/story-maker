"""`linter-legibilidad`: medidas, índice y sus límites (018-C3, 018-C4)."""

from __future__ import annotations

from story_maker.lint.readability import ReadabilityTarget, lint_readability

# 20 palabras, 36 sílabas, 2 frases (el mismo ejemplo que trabaja la spec 018, caso C3).
_TEXT = (
    "Marta caminaba despacio por el sendero largo y miraba las estrellas. "
    "El sol ya daba luz en las hojas secas."
)


def test_calcula_la_longitud_media_de_frase_y_el_indice_sin_disparar_con_margen() -> None:
    target = ReadabilityTarget(age_band="children", max_sentence_length=20, min_fernandez_huerta=0)
    result = lint_readability(_TEXT, target)

    assert result.validator == "linter-legibilidad"
    assert result.passed is True
    assert result.metric == 88.64
    assert result.defects == ()


def test_la_longitud_media_de_frase_en_su_maximo_no_dispara() -> None:
    text = ("casa " * 12).strip() + "."
    target = ReadabilityTarget(
        age_band="children", max_sentence_length=12, min_fernandez_huerta=-1000
    )
    result = lint_readability(text, target)

    assert result.passed is True
    assert result.defects == ()


def test_la_longitud_media_de_frase_por_encima_del_maximo_dispara() -> None:
    text = ("casa " * 13).strip() + "."
    target = ReadabilityTarget(
        age_band="children", max_sentence_length=12, min_fernandez_huerta=-1000
    )
    result = lint_readability(text, target)

    assert result.passed is False
    assert len(result.defects) == 1
    assert result.defects[0].message == (
        "longitud media de frase 13,00 palabras; máximo de la franja children: 12"
    )

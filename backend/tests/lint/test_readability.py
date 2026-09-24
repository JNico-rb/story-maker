"""`linter-legibilidad`: medidas e índice de Fernández-Huerta (018-C3)."""

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

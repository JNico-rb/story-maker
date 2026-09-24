"""`linter-legibilidad`: medidas, índice, sus límites y la franja del objetivo
(018-C3 a 018-C6)."""

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


def _sentence(words: list[str]) -> str:
    return " ".join(words) + "."


def test_el_indice_en_su_minimo_no_dispara() -> None:
    text = " ".join(_sentence(["casa"] * 10) for _ in range(10))
    target = ReadabilityTarget(
        age_band="teen", max_sentence_length=1000, min_fernandez_huerta=76.64
    )
    result = lint_readability(text, target)

    assert result.passed is True
    assert result.metric == 76.64
    assert result.defects == ()


def test_el_indice_por_debajo_del_minimo_dispara() -> None:
    sentences = [_sentence(["casa"] * 10) for _ in range(9)]
    sentences.append(_sentence(["ventana", *["casa"] * 9]))
    text = " ".join(sentences)
    target = ReadabilityTarget(
        age_band="teen", max_sentence_length=1000, min_fernandez_huerta=76.64
    )
    result = lint_readability(text, target)

    assert result.passed is False
    assert result.metric == 76.04
    assert len(result.defects) == 1
    assert result.defects[0].message == (
        "índice de Fernández-Huerta 76,04; mínimo de la franja teen: 76,64"
    )


def test_la_franja_del_destinatario_elige_el_objetivo() -> None:
    text = _sentence(["casa"] * 15)

    children = ReadabilityTarget(
        age_band="children", max_sentence_length=12, min_fernandez_huerta=-1000
    )
    adult = ReadabilityTarget(age_band="adult", max_sentence_length=20, min_fernandez_huerta=-1000)

    children_result = lint_readability(text, children)
    adult_result = lint_readability(text, adult)

    assert children_result.passed is False
    assert children_result.defects[0].message == (
        "longitud media de frase 15,00 palabras; máximo de la franja children: 12"
    )
    assert adult_result.passed is True
    assert adult_result.defects == ()

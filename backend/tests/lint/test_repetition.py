"""`linter-repeticion`: una palabra repetida en un mismo párrafo (018-C1)."""

from __future__ import annotations

from story_maker.lint.repetition import lint_repetition


def test_una_palabra_repetida_tres_veces_en_un_parrafo_da_un_aviso() -> None:
    text = "La Ventana daba al jardín. Cerré la ventana y miré otra vez la ventana."
    result = lint_repetition(text)

    assert result.validator == "linter-repeticion"
    assert result.passed is False
    assert result.metric == 1
    assert len(result.defects) == 1
    assert result.defects[0].message == '"ventana" 3 veces en el párrafo 1'
    assert result.defects[0].paragraph == 1


def test_dos_apariciones_en_parrafos_distintos_no_se_suman() -> None:
    text = "La ventana estaba abierta y la ventana crujía.\n\nCerca había otra ventana y puerta."
    result = lint_repetition(text)

    assert result.passed is True
    assert result.metric == 0
    assert result.defects == ()


def test_cuatro_apariciones_en_un_parrafo_dan_un_solo_aviso_con_el_recuento() -> None:
    text = "ventana ventana ventana ventana"
    result = lint_repetition(text)

    assert len(result.defects) == 1
    assert result.defects[0].message == '"ventana" 4 veces en el párrafo 1'


def test_el_plural_es_otra_palabra_y_no_dispara() -> None:
    text = "La ventana, la ventana y las ventanas del salón."
    result = lint_repetition(text)

    assert result.passed is True


def test_una_palabra_gramatical_repetida_cinco_veces_no_dispara() -> None:
    text = "la casa, la calle, la plaza, la fuente y la torre"
    result = lint_repetition(text)

    assert result.passed is True


def test_un_nombre_canonico_repetido_tres_veces_dispara() -> None:
    text = "Marta corría. Marta reía. Marta cantaba bajo la lluvia."
    result = lint_repetition(text)

    assert result.passed is False
    assert result.defects[0].message == '"marta" 3 veces en el párrafo 1'

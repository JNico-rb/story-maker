"""`linter-repeticion`: una palabra o una muletilla repetida en un párrafo (018-C1, 018-C2)."""

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


def test_una_muletilla_repetida_dos_veces_en_un_parrafo_da_un_aviso() -> None:
    text = "De repente sonó el teléfono. Marta se sobresaltó, y de repente colgaron."
    result = lint_repetition(text)

    assert result.passed is False
    assert len(result.defects) == 1
    assert result.defects[0].message == 'muletilla "de repente" 2 veces en el párrafo 1'


def test_una_sola_palabra_dispara_con_dos_apariciones() -> None:
    text = "Entonces llegó Marta. Entonces se sentó a esperar."
    result = lint_repetition(text)

    assert len(result.defects) == 1
    assert result.defects[0].message == 'muletilla "entonces" 2 veces en el párrafo 1'


def test_una_aparicion_en_cada_parrafo_no_dispara() -> None:
    text = "De repente llovió.\n\nY de repente paró."
    result = lint_repetition(text)

    assert result.passed is True


def test_tres_apariciones_dan_un_solo_aviso_de_muletilla_sin_aviso_aparte_de_palabra_suelta() -> (
    None
):
    text = "De repente, de repente y de repente otra vez pasó algo extraño en la sala."
    result = lint_repetition(text)

    assert len(result.defects) == 1
    assert result.defects[0].message == 'muletilla "de repente" 3 veces en el párrafo 1'

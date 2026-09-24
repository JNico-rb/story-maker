"""`linter-consistencia`: narrador, tratamiento sin y con excepciones (018-C12 a 018-C15)."""

from __future__ import annotations

from story_maker.lint.consistency import StyleSheetInput, lint_consistency

_VALIDATOR = "linter-consistencia"


def _third_person() -> StyleSheetInput:
    return StyleSheetInput(narrator="third_person", default_treatment="tu")


def _first_person() -> StyleSheetInput:
    return StyleSheetInput(narrator="first_person", default_treatment="tu")


def _style_sheet(default_treatment: str, exceptions: tuple[str, ...] = ()) -> StyleSheetInput:
    return StyleSheetInput(
        narrator="third_person",
        default_treatment=default_treatment,
        treatment_exceptions=exceptions,
    )


def test_una_marca_de_primera_persona_en_la_narracion_dispara() -> None:
    text = "Aquella tarde me pareció eterna."
    result = lint_consistency(text, _third_person())

    assert result.validator == _VALIDATOR
    assert result.passed is False
    assert len(result.defects) == 1
    assert result.defects[0].message == (
        'párrafo 1: primera persona en la narración ("me"); la StyleSheet pide tercera persona'
    )
    assert result.defects[0].paragraph == 1


def test_una_marca_dentro_del_dialogo_de_raya_no_dispara() -> None:
    text = "—Me voy a casa —dijo Marta."
    result = lint_consistency(text, _third_person())

    assert result.passed is True


def test_una_marca_dentro_de_comillas_no_dispara() -> None:
    text = "Marta escribió: «Te echo de menos, mi amor»."
    result = lint_consistency(text, _third_person())

    assert result.passed is True


def test_el_inciso_del_narrador_es_narracion_y_dispara() -> None:
    text = "—Vete —me dijo Marta—."
    result = lint_consistency(text, _third_person())

    assert result.passed is False
    assert len(result.defects) == 1


def test_dos_marcas_en_la_narracion_del_mismo_parrafo_dan_un_solo_aviso() -> None:
    text = "Yo lo sabía, y me lo confirmaron después."
    result = lint_consistency(text, _third_person())

    assert len(result.defects) == 1
    assert result.defects[0].message == (
        'párrafo 1: primera persona en la narración ("yo", "me"); '
        "la StyleSheet pide tercera persona"
    )


def test_al_menos_una_marca_de_primera_persona_en_la_narracion_no_dispara() -> None:
    text = "Yo caminaba despacio.\n\nMarta me esperaba en la esquina."
    result = lint_consistency(text, _first_person())

    assert result.passed is True


def test_marcas_solo_en_el_dialogo_disparan_para_primera_persona() -> None:
    text = "—Me voy a casa —dijo Marta.\n\nEl día estaba tranquilo."
    result = lint_consistency(text, _first_person())

    assert result.passed is False
    assert len(result.defects) == 1
    assert result.defects[0].message == (
        "el capítulo no tiene marcas de primera persona en la narración; "
        "la StyleSheet pide primera persona"
    )
    assert result.defects[0].paragraph is None


def test_un_tratamiento_no_admitido_en_el_dialogo_dispara() -> None:
    text = "—¿Usted viene? —preguntó Marta."
    result = lint_consistency(text, _style_sheet(default_treatment="tu"))

    assert result.passed is False
    assert len(result.defects) == 1
    assert result.defects[0].message == (
        'párrafo 1: tratamiento "usted" no admitido por la StyleSheet (tú)'
    )


def test_el_tratamiento_fuera_del_dialogo_no_se_mira() -> None:
    text = "Marta nunca trataba de usted a nadie."
    result = lint_consistency(text, _style_sheet(default_treatment="tu"))

    assert result.passed is True


def test_te_con_tilde_no_es_una_marca_de_tratamiento() -> None:
    text = "—¿Quieres un té?"
    result = lint_consistency(text, _style_sheet(default_treatment="tu"))

    assert result.passed is True


def test_un_tratamiento_de_tu_no_admitido_con_usted_por_defecto_dispara() -> None:
    text = "—Te espero aquí."
    result = lint_consistency(text, _style_sheet(default_treatment="usted"))

    assert result.passed is False
    assert len(result.defects) == 1
    assert result.defects[0].message == (
        'párrafo 1: tratamiento "tú" no admitido por la StyleSheet (usted)'
    )


def test_un_tratamiento_admitido_por_excepcion_no_dispara() -> None:
    text = "—¿Usted viene?"
    result = lint_consistency(text, _style_sheet(default_treatment="tu", exceptions=("usted",)))

    assert result.passed is True


def test_mezclar_tu_y_usted_en_la_misma_intervencion_dispara() -> None:
    text = "—Usted sabe que te quiero."
    result = lint_consistency(text, _style_sheet(default_treatment="tu", exceptions=("usted",)))

    assert result.passed is False
    assert len(result.defects) == 1
    assert result.defects[0].message == "párrafo 1: mezcla tú y usted en la misma intervención"


def test_sin_excepciones_el_no_admitido_gana_a_la_mezcla() -> None:
    text = "—Usted sabe que te quiero."
    result = lint_consistency(text, _style_sheet(default_treatment="tu"))

    assert result.passed is False
    assert len(result.defects) == 1
    assert result.defects[0].message == (
        'párrafo 1: tratamiento "usted" no admitido por la StyleSheet (tú)'
    )

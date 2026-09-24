"""`linter-consistencia`: narrador en tercera persona (018-C12)."""

from __future__ import annotations

from story_maker.lint.consistency import StyleSheetInput, lint_consistency

_VALIDATOR = "linter-consistencia"


def _third_person() -> StyleSheetInput:
    return StyleSheetInput(narrator="third_person", default_treatment="tu")


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

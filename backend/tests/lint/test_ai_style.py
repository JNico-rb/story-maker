"""`linter-estilo-ia`: adverbios en -mente, palabras en -mente que no lo son y clichés
(018-C9 a 018-C11)."""

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


def test_dos_cliches_distintos_dan_un_aviso_cada_uno_con_sus_parrafos() -> None:
    text = (
        "Marta cruzó la plaza desierta.\n\n"
        "Un escalofrío le recorrió la espalda al ver la puerta abierta.\n\n"
        "Se acercó despacio, sin hacer ruido.\n\n"
        "El tiempo pareció detenerse mientras escuchaba.\n\n"
        "Entonces oyó un ruido: un escalofrío le recorrió la espalda otra vez."
    )
    result = lint_ai_style(text)

    assert len(result.defects) == 2
    assert result.defects[0].message == (
        'cliché "un escalofrío le recorrió la espalda" 2 veces (párrafos 2 y 5)'
    )
    assert result.defects[1].message == ('cliché "el tiempo pareció detenerse" 1 vez (párrafo 4)')


def test_un_cliche_con_una_palabra_intercalada_no_dispara() -> None:
    text = "Un escalofrío frío le recorrió la espalda al entrar."
    result = lint_ai_style(text)

    assert result.defects == ()


def test_un_cliche_en_mayusculas_dispara() -> None:
    text = "UN ESCALOFRÍO LE RECORRIÓ LA ESPALDA al fin."
    result = lint_ai_style(text)

    assert len(result.defects) == 1
    assert result.defects[0].message == (
        'cliché "un escalofrío le recorrió la espalda" 1 vez (párrafo 1)'
    )

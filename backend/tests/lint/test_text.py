"""Utilidades de texto compartidas por los linters: sílabas y frases (018-C7, 018-C8)."""

from __future__ import annotations

import pytest

from story_maker.lint.text import count_sentences, count_syllables


@pytest.mark.parametrize(
    ("word", "syllables"),
    [
        ("casa", 2),  # un núcleo por vocal separada
        ("cielo", 2),  # débil y fuerte: un solo núcleo
        ("ciudad", 2),  # dos débiles: un solo núcleo
        ("poeta", 3),  # dos fuertes se separan
        ("aéreo", 4),  # fuertes seguidas, todas separadas
        ("río", 2),  # una débil con tilde se separa de la fuerte
        ("caída", 3),  # la débil con tilde se separa de las dos fuertes
        ("buey", 1),  # serie sin punto de separación; y final como vocal
        ("pingüino", 3),  # ü es vocal débil
        ("y", 1),  # y final como vocal
        ("ya", 1),  # y inicial, consonante
    ],
)
def test_recuento_de_silabas(word: str, syllables: int) -> None:
    assert count_syllables(word) == syllables


@pytest.mark.parametrize(
    ("paragraph", "sentences"),
    [
        ("Hola. Adiós.", 2),  # punto, espacio y mayúscula
        ("—¿Vienes? —preguntó Marta.", 1),  # se salta la raya de inciso y sigue minúscula
        ("¡Ya! ¿Qué?", 2),  # tras el signo final viene «¿», que no es minúscula
        ("Esperó… y siguió.", 1),  # sigue una minúscula
        ("Llegó a las 8 p. m. y se fue.", 1),  # la abreviatura va seguida de minúscula
        ("Nadie vino", 1),  # el párrafo sin signo final cierra su frase
    ],
)
def test_recuento_de_frases(paragraph: str, sentences: int) -> None:
    assert count_sentences(paragraph) == sentences


def test_una_serie_de_signos_corta_una_vez_y_cada_parrafo_cierra_su_frase() -> None:
    assert count_sentences("Esperó...") + count_sentences("Nadie vino") == 2

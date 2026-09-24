"""Utilidades de texto compartidas por los linters: sílabas y frases (018-C7, 018-C8)."""

from __future__ import annotations

import pytest

from story_maker.lint.text import count_syllables


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

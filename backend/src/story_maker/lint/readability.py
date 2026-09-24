"""`linter-legibilidad`: longitud de frase e índice de Fernández-Huerta (018-C3 a 018-C6)."""

from __future__ import annotations

from dataclasses import dataclass

from story_maker.lint.text import count_sentences, count_syllables, extract_words, split_paragraphs
from story_maker.lint.types import Defect, LinterResult

_VALIDATOR = "linter-legibilidad"


@dataclass(frozen=True)
class ReadabilityTarget:
    """Objetivos de legibilidad de una `FranjaDeEdad` (`quality.readability_targets.<franja>`)."""

    age_band: str
    max_sentence_length: float
    min_fernandez_huerta: float


def lint_readability(text: str, target: ReadabilityTarget) -> LinterResult:
    """Avisa si la longitud media de frase supera el máximo, o el índice de Fernández-Huerta
    no llega al mínimo, de la franja del destinatario (018-C3 a 018-C6)."""
    words = extract_words(text)
    sentences = sum(count_sentences(paragraph) for paragraph in split_paragraphs(text))
    if not words or not sentences:
        return LinterResult(validator=_VALIDATOR, passed=True, metric=None, defects=())

    syllables = sum(count_syllables(word) for word in words)
    sentence_length = round(len(words) / sentences, 2)
    index = round(
        206.84 - 60 * (syllables / len(words)) - 1.02 * (len(words) / sentences),
        2,
    )

    defects = []
    if sentence_length > target.max_sentence_length:
        defects.append(
            Defect(
                message=(
                    f"longitud media de frase {_format_measure(sentence_length)} palabras; "
                    f"máximo de la franja {target.age_band}: "
                    f"{_format_threshold(target.max_sentence_length)}"
                )
            )
        )
    if index < target.min_fernandez_huerta:
        defects.append(
            Defect(
                message=(
                    f"índice de Fernández-Huerta {_format_measure(index)}; "
                    f"mínimo de la franja {target.age_band}: "
                    f"{_format_threshold(target.min_fernandez_huerta)}"
                )
            )
        )
    return LinterResult(
        validator=_VALIDATOR, passed=not defects, metric=index, defects=tuple(defects)
    )


def _format_measure(value: float) -> str:
    """Formato español de una medida: siempre dos decimales, con coma."""
    return f"{value:.2f}".replace(".", ",")


def _format_threshold(value: float) -> str:
    """Formato español de un umbral: entero si lo es; si no, dos decimales con coma."""
    if value == int(value):
        return str(int(value))
    return _format_measure(value)

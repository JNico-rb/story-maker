"""Los cuatro linters sobre el texto de un capítulo, en el orden de la spec 018: el mismo en el
punto `editor` del bucle y en el lint en vivo de 019 (018-I2, I3)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from story_maker.lint.ai_style import lint_ai_style
from story_maker.lint.consistency import StyleSheetInput, lint_consistency
from story_maker.lint.readability import ReadabilityTarget, lint_readability
from story_maker.lint.repetition import lint_repetition
from story_maker.lint.types import LinterResult

LINTERS = ("linter-repeticion", "linter-legibilidad", "linter-estilo-ia", "linter-consistencia")


@dataclass(frozen=True)
class LintInputs:
    """Lo que los linters leen además del texto: la StyleSheet y la franja del destinatario."""

    style_sheet: StyleSheetInput
    target: ReadabilityTarget


def chapter_linters(inputs: LintInputs) -> tuple[tuple[str, Callable[[str], LinterResult]], ...]:
    """Cada linter con su nombre, en el orden de sus avisos, listo para correr sobre un texto."""
    linters: tuple[Callable[[str], LinterResult], ...] = (
        lint_repetition,
        lambda text: lint_readability(text, inputs.target),
        lint_ai_style,
        lambda text: lint_consistency(text, inputs.style_sheet),
    )
    return tuple(zip(LINTERS, linters, strict=True))


def lint_chapter(text: str, inputs: LintInputs) -> tuple[LinterResult, ...]:
    return tuple(linter(text) for _, linter in chapter_linters(inputs))

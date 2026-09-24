"""`linter-repeticion`: una palabra o muletilla repetida en un párrafo (018-C1, 018-C2)."""

from __future__ import annotations

from collections import Counter

from story_maker.domain.prose_lint import GRAMMATICAL_WORDS, WORD_REPETITION_THRESHOLD
from story_maker.lint.text import comparison_form, extract_words, split_paragraphs
from story_maker.lint.types import Defect, LinterResult

_VALIDATOR = "linter-repeticion"


def _word_defects(paragraph: str, paragraph_number: int) -> list[Defect]:
    words = extract_words(paragraph)
    counts = Counter(comparison_form(word) for word in words)
    defects = []
    for word, count in counts.items():
        if word in GRAMMATICAL_WORDS or count < WORD_REPETITION_THRESHOLD:
            continue
        message = f'"{word}" {count} veces en el párrafo {paragraph_number}'
        defects.append(Defect(message=message, paragraph=paragraph_number))
    return defects


def lint_repetition(text: str) -> LinterResult:
    """Avisa de una palabra repetida 3 veces o más en un mismo párrafo (018-C1)."""
    defects: list[Defect] = []
    for number, paragraph in enumerate(split_paragraphs(text), start=1):
        defects.extend(_word_defects(paragraph, number))
    return LinterResult(
        validator=_VALIDATOR, passed=not defects, metric=len(defects), defects=tuple(defects)
    )

"""`linter-repeticion`: una palabra o muletilla repetida en un párrafo (018-C1, 018-C2)."""

from __future__ import annotations

from story_maker.domain.prose_lint import (
    FILLER_PHRASES,
    FILLER_REPETITION_THRESHOLD,
    GRAMMATICAL_WORDS,
    WORD_REPETITION_THRESHOLD,
)
from story_maker.lint.text import comparison_form, extract_words, find_sequences, split_paragraphs
from story_maker.lint.types import Defect, LinterResult

_VALIDATOR = "linter-repeticion"


def _filler_defects(
    words: list[str], paragraph_number: int, consumed: set[int]
) -> list[tuple[int, Defect]]:
    candidates = []
    for phrase in FILLER_PHRASES:
        starts = find_sequences(words, phrase)
        if len(starts) < FILLER_REPETITION_THRESHOLD:
            continue
        width = len(extract_words(phrase))
        for start in starts:
            consumed.update(range(start, start + width))
        message = f'muletilla "{phrase}" {len(starts)} veces en el párrafo {paragraph_number}'
        candidates.append((starts[0], Defect(message=message, paragraph=paragraph_number)))
    return candidates


def _word_defects(
    words: list[str], paragraph_number: int, consumed: set[int]
) -> list[tuple[int, Defect]]:
    positions: dict[str, list[int]] = {}
    for index, word in enumerate(words):
        if index in consumed:
            continue
        positions.setdefault(comparison_form(word), []).append(index)
    candidates = []
    for word, indices in positions.items():
        if word in GRAMMATICAL_WORDS or len(indices) < WORD_REPETITION_THRESHOLD:
            continue
        message = f'"{word}" {len(indices)} veces en el párrafo {paragraph_number}'
        candidates.append((indices[0], Defect(message=message, paragraph=paragraph_number)))
    return candidates


def _paragraph_defects(paragraph: str, paragraph_number: int) -> list[Defect]:
    words = extract_words(paragraph)
    consumed: set[int] = set()
    candidates = _filler_defects(words, paragraph_number, consumed)
    candidates += _word_defects(words, paragraph_number, consumed)
    candidates.sort(key=lambda item: item[0])
    return [defect for _, defect in candidates]


def lint_repetition(text: str) -> LinterResult:
    """Avisa de una palabra repetida 3 veces, o una muletilla 2 veces, en un párrafo
    (018-C1, 018-C2)."""
    defects: list[Defect] = []
    for number, paragraph in enumerate(split_paragraphs(text), start=1):
        defects.extend(_paragraph_defects(paragraph, number))
    return LinterResult(
        validator=_VALIDATOR, passed=not defects, metric=len(defects), defects=tuple(defects)
    )

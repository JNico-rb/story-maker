"""`linter-estilo-ia`: adverbios en -mente y clichés de texto generado (018-C9 a 018-C11)."""

from __future__ import annotations

from story_maker.domain.prose_lint import CLICHES, MENTE_DENSITY_THRESHOLD, MENTE_EXCEPTIONS
from story_maker.lint.text import comparison_form, extract_words, find_sequences, split_paragraphs
from story_maker.lint.types import Defect, LinterResult

_VALIDATOR = "linter-estilo-ia"
_MENTE_SUFFIX = "mente"


def _is_mente_adverb(word: str) -> bool:
    form = comparison_form(word)
    if form in MENTE_EXCEPTIONS:
        return False
    return form.endswith(_MENTE_SUFFIX) and len(form) > len(_MENTE_SUFFIX)


def _density_defect(words: list[str]) -> tuple[float, Defect | None]:
    adverbs = sum(1 for word in words if _is_mente_adverb(word))
    density = round(adverbs / len(words) * 1000, 2)
    if density <= MENTE_DENSITY_THRESHOLD:
        return density, None
    threshold = int(MENTE_DENSITY_THRESHOLD)
    message = (
        f"{density:.2f}".replace(".", ",")
        + f" adverbios en -mente por 1.000 palabras; umbral: {threshold}"
    )
    return density, Defect(message=message)


def _join_spanish(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f" y {items[-1]}"


def _cliche_defect(phrase: str, paragraphs: list[str]) -> tuple[tuple[int, int], Defect] | None:
    occurrences: list[int] = []
    first_key: tuple[int, int] | None = None
    for number, paragraph in enumerate(paragraphs, start=1):
        starts = find_sequences(extract_words(paragraph), phrase)
        for start in starts:
            occurrences.append(number)
            if first_key is None:
                first_key = (number, start)
    if not occurrences or first_key is None:
        return None
    count = len(occurrences)
    times = "vez" if count == 1 else "veces"
    label = "párrafo" if count == 1 else "párrafos"
    where = _join_spanish([str(number) for number in occurrences])
    message = f'cliché "{phrase}" {count} {times} ({label} {where})'
    return first_key, Defect(message=message)


def _cliche_defects(text: str) -> list[Defect]:
    paragraphs = split_paragraphs(text)
    candidates = []
    for phrase in CLICHES:
        found = _cliche_defect(phrase, paragraphs)
        if found is not None:
            candidates.append(found)
    candidates.sort(key=lambda item: item[0])
    return [defect for _, defect in candidates]


def lint_ai_style(text: str) -> LinterResult:
    """Avisa si la densidad de adverbios en -mente supera su umbral, o si hay un cliché
    de la lista cerrada del dominio (018-C9 a 018-C11)."""
    words = extract_words(text)
    if not words:
        return LinterResult(validator=_VALIDATOR, passed=True, metric=None, defects=())

    density, density_defect = _density_defect(words)
    defects = [density_defect] if density_defect is not None else []
    defects.extend(_cliche_defects(text))

    return LinterResult(
        validator=_VALIDATOR, passed=not defects, metric=density, defects=tuple(defects)
    )

"""`linter-estilo-ia`: adverbios en -mente y clichés de texto generado (018-C9 a 018-C11)."""

from __future__ import annotations

from story_maker.domain.prose_lint import MENTE_DENSITY_THRESHOLD
from story_maker.lint.text import comparison_form, extract_words
from story_maker.lint.types import Defect, LinterResult

_VALIDATOR = "linter-estilo-ia"
_MENTE_SUFFIX = "mente"


def _is_mente_adverb(word: str) -> bool:
    form = comparison_form(word)
    return form.endswith(_MENTE_SUFFIX) and len(form) > len(_MENTE_SUFFIX)


def lint_ai_style(text: str) -> LinterResult:
    """Avisa si la densidad de adverbios en -mente supera su umbral (018-C9)."""
    words = extract_words(text)
    if not words:
        return LinterResult(validator=_VALIDATOR, passed=True, metric=None, defects=())

    adverbs = sum(1 for word in words if _is_mente_adverb(word))
    density = round(adverbs / len(words) * 1000, 2)

    defects = []
    if density > MENTE_DENSITY_THRESHOLD:
        threshold = int(MENTE_DENSITY_THRESHOLD)
        message = (
            f"{density:.2f}".replace(".", ",")
            + f" adverbios en -mente por 1.000 palabras; umbral: {threshold}"
        )
        defects.append(Defect(message=message))

    return LinterResult(
        validator=_VALIDATOR, passed=not defects, metric=density, defects=tuple(defects)
    )

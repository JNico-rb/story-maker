"""`linter-consistencia`: narrador y tratamiento frente a la StyleSheet (018-C12 a 018-C15)."""

from __future__ import annotations

from dataclasses import dataclass, field

from story_maker.domain.prose_lint import FIRST_PERSON_MARKS
from story_maker.lint.dialogue import narration_text
from story_maker.lint.text import comparison_form, extract_words, split_paragraphs
from story_maker.lint.types import Defect, LinterResult

_VALIDATOR = "linter-consistencia"


@dataclass(frozen=True)
class StyleSheetInput:
    """Lo que `linter-consistencia` necesita de la StyleSheet de la versión."""

    narrator: str  # "first_person" | "third_person"
    default_treatment: str  # "tu" | "usted"
    treatment_exceptions: tuple[str, ...] = field(default_factory=tuple)


def _first_person_marks(text: str) -> list[str]:
    marks = []
    seen = set()
    for word in extract_words(text):
        form = comparison_form(word)
        if form in FIRST_PERSON_MARKS and form not in seen:
            seen.add(form)
            marks.append(form)
    return marks


def _narrator_defects(paragraphs: list[str], style_sheet: StyleSheetInput) -> list[Defect]:
    if style_sheet.narrator != "third_person":
        return []
    defects = []
    for number, paragraph in enumerate(paragraphs, start=1):
        marks = _first_person_marks(narration_text(paragraph))
        if not marks:
            continue
        quoted = ", ".join(f'"{mark}"' for mark in marks)
        message = (
            f"párrafo {number}: primera persona en la narración ({quoted}); "
            "la StyleSheet pide tercera persona"
        )
        defects.append(Defect(message=message, paragraph=number))
    return defects


def _missing_first_person_defect(
    paragraphs: list[str], style_sheet: StyleSheetInput
) -> Defect | None:
    if style_sheet.narrator != "first_person":
        return None
    for paragraph in paragraphs:
        if _first_person_marks(narration_text(paragraph)):
            return None
    return Defect(
        message=(
            "el capítulo no tiene marcas de primera persona en la narración; "
            "la StyleSheet pide primera persona"
        )
    )


def lint_consistency(text: str, style_sheet: StyleSheetInput) -> LinterResult:
    """Avisa si la narración no respeta el narrador de la StyleSheet (018-C12, 018-C13)."""
    paragraphs = split_paragraphs(text)
    defects = _narrator_defects(paragraphs, style_sheet)
    missing = _missing_first_person_defect(paragraphs, style_sheet)
    if missing is not None:
        defects.append(missing)
    return LinterResult(
        validator=_VALIDATOR, passed=not defects, metric=len(defects), defects=tuple(defects)
    )

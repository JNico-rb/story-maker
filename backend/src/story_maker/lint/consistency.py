"""`linter-consistencia`: narrador y tratamiento frente a la StyleSheet (018-C12 a 018-C15)."""

from __future__ import annotations

from dataclasses import dataclass, field

from story_maker.domain.prose_lint import (
    FIRST_PERSON_MARKS,
    TREATMENT_DISPLAY_NAMES,
    TU_TREATMENT_MARKS,
    USTED_TREATMENT_MARKS,
)
from story_maker.lint.dialogue import interventions, narration_text
from story_maker.lint.text import comparison_form, extract_words, split_paragraphs
from story_maker.lint.types import Defect, LinterResult

_TREATMENT_MARKS = {"tu": TU_TREATMENT_MARKS, "usted": USTED_TREATMENT_MARKS}

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


def _found_treatments(intervention: str) -> set[str]:
    words = {comparison_form(word) for word in extract_words(intervention)}
    found = set()
    for treatment, marks in _TREATMENT_MARKS.items():
        if words & marks:
            found.add(treatment)
    return found


def _treatment_defect(
    intervention: str, paragraph_number: int, style_sheet: StyleSheetInput
) -> Defect | None:
    admitted = {style_sheet.default_treatment, *style_sheet.treatment_exceptions}
    found = _found_treatments(intervention)
    not_admitted = found - admitted
    if not_admitted:
        treatment = sorted(not_admitted)[0]
        display = TREATMENT_DISPLAY_NAMES[treatment]
        default_display = TREATMENT_DISPLAY_NAMES[style_sheet.default_treatment]
        message = (
            f'párrafo {paragraph_number}: tratamiento "{display}" no admitido '
            f"por la StyleSheet ({default_display})"
        )
        return Defect(message=message, paragraph=paragraph_number)
    if len(found) > 1:
        message = f"párrafo {paragraph_number}: mezcla tú y usted en la misma intervención"
        return Defect(message=message, paragraph=paragraph_number)
    return None


def _treatment_defects(paragraphs: list[str], style_sheet: StyleSheetInput) -> list[Defect]:
    defects = []
    for number, paragraph in enumerate(paragraphs, start=1):
        for intervention in interventions(paragraph):
            defect = _treatment_defect(intervention, number, style_sheet)
            if defect is not None:
                defects.append(defect)
    return defects


def lint_consistency(text: str, style_sheet: StyleSheetInput) -> LinterResult:
    """Avisa si la narración o el tratamiento no respetan la StyleSheet (018-C12 a 018-C15)."""
    paragraphs = split_paragraphs(text)
    defects = _narrator_defects(paragraphs, style_sheet)
    missing = _missing_first_person_defect(paragraphs, style_sheet)
    if missing is not None:
        defects.append(missing)
    defects.extend(_treatment_defects(paragraphs, style_sheet))
    return LinterResult(
        validator=_VALIDATOR, passed=not defects, metric=len(defects), defects=tuple(defects)
    )

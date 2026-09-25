"""El punto `editor` de los linters de prosa en el bucle del capítulo (spec 018, C18 a C23): sus
entradas desde la candidata y la config, y su resultado como `ValidatorRun` no bloqueante, con
la métrica como score y el umbral como comentario (`architecture.md` §11.2)."""

from __future__ import annotations

from typing import Any, cast

from sqlalchemy.orm import Session

from story_maker.config import Config
from story_maker.domain.brief import age_band
from story_maker.domain.prose_lint import (
    FILLER_REPETITION_THRESHOLD,
    MENTE_DENSITY_THRESHOLD,
    TREATMENT_DISPLAY_NAMES,
    WORD_REPETITION_THRESHOLD,
)
from story_maker.lint.chapter import LintInputs
from story_maker.lint.consistency import StyleSheetInput
from story_maker.lint.readability import ReadabilityTarget
from story_maker.lint.types import LinterResult
from story_maker.pipeline.acceptance import ValidatorRun
from story_maker.store.models import Character, Novel, StyleSheet, Version

ADULT_AGE = 18
NARRATORS = {"first": "first_person", "third": "third_person"}
NARRATOR_NAMES = {"first_person": "primera persona", "third_person": "tercera persona"}


def _recipient_age(session: Session, version_id: int) -> int:
    """La edad del destinatario en el año presente, como la calcula la planificación (010); sin
    fecha de nacimiento, adulto."""
    version = session.get_one(Version, version_id)
    novel = session.get_one(Novel, version.novel_id)
    recipient = (
        session.query(Character)
        .filter(Character.version_id == version_id, Character.type == "recipient")
        .first()
    )
    if recipient is None or recipient.birth_date is None:
        return ADULT_AGE
    return novel.created_at.year - recipient.birth_date.year


def _style_sheet(session: Session, version_id: int) -> StyleSheetInput:
    row = session.query(StyleSheet).filter(StyleSheet.version_id == version_id).one_or_none()
    content = cast(dict[str, Any], row.content) if row is not None else {}
    exceptions = content.get("treatment_exceptions") or []
    return StyleSheetInput(
        narrator=NARRATORS.get(str(content.get("narrator")), "third_person"),
        default_treatment=str(content.get("default_treatment") or "tu"),
        treatment_exceptions=tuple(str(e["treatment"]) for e in exceptions),
    )


def lint_inputs(session: Session, version_id: int, config: Config) -> LintInputs:
    """La StyleSheet de la versión y los objetivos de la franja de su destinatario (018-C6)."""
    band = age_band(_recipient_age(session, version_id))
    target = config.readability_targets[band]
    return LintInputs(
        style_sheet=_style_sheet(session, version_id),
        target=ReadabilityTarget(
            age_band=band,
            max_sentence_length=target.sentence_length,
            min_fernandez_huerta=target.fernandez_huerta,
        ),
    )


def threshold_comment(result: LinterResult, inputs: LintInputs) -> str:
    """El umbral de cada linter, que va en el comentario de su score (tabla de 018)."""
    if result.validator == "linter-repeticion":
        return (
            f"una palabra {WORD_REPETITION_THRESHOLD} veces o una muletilla "
            f"{FILLER_REPETITION_THRESHOLD} veces en un párrafo"
        )
    if result.validator == "linter-legibilidad":
        target = inputs.target
        return (
            f"franja {target.age_band}: longitud media de frase máxima "
            f"{target.max_sentence_length}; índice de Fernández-Huerta mínimo "
            f"{target.min_fernandez_huerta}"
        )
    if result.validator == "linter-estilo-ia":
        cliches = sum(1 for d in result.defects if d.message.startswith("cliché"))
        return (
            f"umbral {int(MENTE_DENSITY_THRESHOLD)} por 1.000 palabras; "
            f"clichés encontrados: {cliches}"
        )
    sheet = inputs.style_sheet
    admitted = dict.fromkeys((sheet.default_treatment, *sheet.treatment_exceptions))
    treatments = ", ".join(TREATMENT_DISPLAY_NAMES[t] for t in admitted)
    return f"narrador en {NARRATOR_NAMES[sheet.narrator]}; tratamientos admitidos: {treatments}"


def lint_run(result: LinterResult, inputs: LintInputs) -> ValidatorRun:
    """Cada aviso, un defecto no bloqueante sin criterio (018-I1)."""
    return ValidatorRun(
        validator=result.validator,
        passed=result.passed,
        comment=threshold_comment(result, inputs),
        defects=tuple(
            {"validator": result.validator, "criterion": None, "blocking": False, "message": m}
            for m in (d.message for d in result.defects)
        ),
        metric=result.metric,
    )

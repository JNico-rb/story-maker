"""Nombres canónicos de validador y de score (`definitions.md` §12.3); TLC no envía score."""

from __future__ import annotations

from typing import Literal

from story_maker.observability.langfuse_adapter import LangfuseObservability
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Score, Span, Trace

ScoreName = Literal[
    "schema-brief",
    "schema-salida",
    "citas-verificadas",
    "outline",
    "longitud-capitulo",
    "nombres-exactos",
    "palabras-prohibidas",
    "elementos-obligatorios",
    "revision-visual",
    "pdf-enlaces",
    "linter-repeticion",
    "linter-legibilidad",
    "linter-estilo-ia",
    "linter-consistencia",
    "rubrica-capitulo",
    "juez-novela",
    "revision-humana",
    "cronologia-lean",
]

SCORE_NAMES: tuple[ScoreName, ...] = (
    "schema-brief",
    "schema-salida",
    "citas-verificadas",
    "outline",
    "longitud-capitulo",
    "nombres-exactos",
    "palabras-prohibidas",
    "elementos-obligatorios",
    "revision-visual",
    "pdf-enlaces",
    "linter-repeticion",
    "linter-legibilidad",
    "linter-estilo-ia",
    "linter-consistencia",
    "rubrica-capitulo",
    "juez-novela",
    "revision-humana",
    "cronologia-lean",
)

NOT_SCORED = "harness-tla"


def is_scoreable(validator_name: str) -> bool:
    """TLC (`harness-tla`) nunca envía score: corre en desarrollo y CI (004-C13)."""
    return validator_name != NOT_SCORED


def export_validator_score(
    observability: LangfuseObservability | NullObservability,
    trace: Trace,
    name: ScoreName,
    value: float,
    comment: str,
    *,
    span: Span | None = None,
) -> Score:
    """El único nombre válido es uno de `SCORE_NAMES`: mypy lo exige (004-I5)."""
    return observability.score(trace, name, value, comment=comment, span=span)

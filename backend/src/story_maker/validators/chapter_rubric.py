"""`rubrica-capitulo`: la revisión del editor y lo que el código deriva de ella
(`architecture.md` §8.2, §11.3; 011-C15, 011-C16).

El editor puntúa y tipa; qué defecto bloquea lo decide el código: solo los criterios bloqueantes
bloquean, bajo su umbral o con un defecto que el editor marca bloqueante (equilibrio del
encargo: no hay media que decida)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

RUBRIC = "rubrica-capitulo"

ChapterCriterion = Literal[
    "fidelidad-canon", "cumple-beats", "personalizacion-natural", "prosa", "tono"
]
CHAPTER_CRITERIA: tuple[ChapterCriterion, ...] = (
    "fidelidad-canon",
    "cumple-beats",
    "personalizacion-natural",
    "prosa",
    "tono",
)
BLOCKING_CRITERIA: frozenset[str] = frozenset({"fidelidad-canon", "cumple-beats"})

# Lo que juzga cada criterio (§11.3), para la ventana del editor.
CRITERION_MEANING: dict[str, str] = {
    "fidelidad-canon": "No contradice la story bible ni capítulos previos",
    "cumple-beats": "Narra los beats planificados",
    "personalizacion-natural": "Los datos del destinatario integrados sin forzar",
    "prosa": "Ni mecánica ni repetitiva",
    "tono": "Conforme al brief",
}


class CriterionScore(BaseModel):
    criterion: ChapterCriterion
    score: int = Field(ge=1, le=5)
    justification: str = Field(min_length=1)


class ReviewDefect(BaseModel):
    criterion: ChapterCriterion
    blocking: bool
    message: str = Field(min_length=1)


class Presence(BaseModel):
    character_id: int
    age: int | None = Field(default=None, ge=0)


class NarratedEvent(BaseModel):
    statement: str = Field(min_length=1)
    moment: dt.datetime
    place_id: int
    present: list[Presence] = Field(default_factory=list)
    type: Literal["ordinary", "exclusion"]
    excluded_character_id: int | None = None
    analepsis: bool
    beat: int

    @model_validator(mode="after")
    def _exclusion_names_its_excluded(self) -> Self:
        if self.type == "exclusion" and self.excluded_character_id is None:
            raise ValueError("un evento exclusion lleva su excluido")
        if self.type == "ordinary" and self.excluded_character_id is not None:
            raise ValueError("un evento ordinary no lleva excluido")
        ids = [p.character_id for p in self.present]
        if len(ids) != len(set(ids)):
            raise ValueError("un presente aparece dos veces en el mismo evento")
        return self


class ChapterReview(BaseModel):
    """Lo que entrega el editor por `submit_review` (§7.2)."""

    scores: list[CriterionScore]
    defects: list[ReviewDefect] = Field(default_factory=list)
    fact_usages: list[int] = Field(default_factory=list)
    events: list[NarratedEvent] = Field(default_factory=list)
    summary: str = Field(min_length=1)

    @model_validator(mode="after")
    def _one_score_per_criterion(self) -> Self:
        given = [s.criterion for s in self.scores]
        missing = [c for c in CHAPTER_CRITERIA if c not in given]
        repeated = sorted({c for c in given if given.count(c) > 1})
        if missing or repeated:
            raise ValueError(
                "una puntuación por criterio de la rúbrica de capítulo: "
                f"faltan {missing or 'ninguno'}; repetidos {repeated or 'ninguno'}"
            )
        return self


@dataclass(frozen=True)
class RubricDefect:
    criterion: str
    blocking: bool
    message: str


@dataclass(frozen=True)
class RubricJudgement:
    """El juicio agregado por código: pasa si no hay ningún defecto bloqueante."""

    scores: tuple[CriterionScore, ...]
    defects: tuple[RubricDefect, ...]

    @property
    def blocking(self) -> tuple[RubricDefect, ...]:
        return tuple(d for d in self.defects if d.blocking)

    @property
    def passed(self) -> bool:
        return not self.blocking


def judge_review(review: ChapterReview, thresholds: Mapping[str, int]) -> RubricJudgement:
    """Un criterio bajo su umbral crea un defecto con la justificación del editor, bloqueante
    solo si el criterio lo es; un defecto marcado bloqueante solo bloquea en un criterio
    bloqueante. Determinista: la misma revisión con los mismos umbrales da siempre lo mismo."""
    below = [
        RubricDefect(s.criterion, s.criterion in BLOCKING_CRITERIA, s.justification)
        for s in review.scores
        if s.score < thresholds[s.criterion]
    ]
    typed = [
        RubricDefect(d.criterion, d.blocking and d.criterion in BLOCKING_CRITERIA, d.message)
        for d in review.defects
    ]
    return RubricJudgement(scores=tuple(review.scores), defects=tuple(below + typed))

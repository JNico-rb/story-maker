"""`juez-novela`: el schema de `submit_evaluation`, la ventana de contexto de su sesión y la
agregación de su entrega en un veredicto (012-C13, 012-C14, 012-C15, 012-C16, 012-I5;
`architecture.md` §6.2, §7.2, §7.4, §9.4, §11.3).

El puerto de agente (003) ya aplica la lista blanca, el hook de policy, la validación por schema
(rechaza y deja reintentar en la misma sesión: 012-C15 no necesita más código que un schema
correcto) y registra la `SesionDeRol`; aquí solo lo propio del juez: qué entra en su única tool,
qué lee en la llamada (012-C16) y cómo el código agrega su entrega sin tocar el texto de ninguna
justificación (012-I5)."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from story_maker.agents.tools import ToolSpec
from story_maker.domain.constants import CHAPTERS_PER_NOVEL
from story_maker.domain.rubric import NOVEL_RUBRIC
from story_maker.domain.trope_catalog import Trope
from story_maker.formal.defects import Defect
from story_maker.pipeline.planning.brief_view import BriefView
from story_maker.store.story_bible import StoryBible

VALIDATOR = "juez-novela"
SUBMIT_EVALUATION = "submit_evaluation"

_RUBRIC_NAMES = tuple(criterion.name for criterion in NOVEL_RUBRIC)


class CriterionSubmission(BaseModel):
    """La entrega de un criterio de la rúbrica: puntuación de 1 a 5, justificación no vacía y al
    menos un capítulo citado, sin repetidos ni fuera de 1-10 (012-C15, 012-C16)."""

    score: int = Field(ge=1, le=5)
    justification: str = Field(min_length=1)
    chapters: tuple[int, ...] = Field(min_length=1)

    @field_validator("chapters")
    @classmethod
    def _cited_chapters_are_valid(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if len(set(value)) != len(value):
            raise ValueError("cita un capítulo repetido")
        if any(not 1 <= chapter <= CHAPTERS_PER_NOVEL for chapter in value):
            raise ValueError(f"cita un capítulo fuera de 1-{CHAPTERS_PER_NOVEL}")
        return value


class JudgeEvaluation(BaseModel):
    """`submit_evaluation`: el schema es estático y exige exactamente los siete criterios de la
    rúbrica (012-C25), ni uno de menos ni uno desconocido (012-C15)."""

    model_config = ConfigDict(extra="forbid")

    continuidad: CriterionSubmission
    coherencia_personajes: CriterionSubmission = Field(alias="coherencia-personajes")
    arco_y_final: CriterionSubmission = Field(alias="arco-y-final")
    ritmo: CriterionSubmission
    tono: CriterionSubmission
    personalizacion_natural: CriterionSubmission = Field(alias="personalizacion-natural")
    no_cliche: CriterionSubmission = Field(alias="no-cliche")

    def get(self, criterion: str) -> CriterionSubmission:
        value: CriterionSubmission = getattr(self, criterion.replace("-", "_"))
        return value


def submit_evaluation_tool() -> ToolSpec:
    """La única tool de la sesión del juez (012-C16)."""
    return ToolSpec(
        name=SUBMIT_EVALUATION,
        model=JudgeEvaluation,
        description="Entrega la evaluación de la novela contra la rúbrica.",
    )


# --- Ventana de la sesión del juez (012-C16) -----------------------------------------------------


@dataclass(frozen=True)
class JudgeChapter:
    number: int
    title: str
    text: str


def build_judge_window(
    title: str,
    chapters: tuple[JudgeChapter, ...],
    story_bible: StoryBible,
    catalog: tuple[Trope, ...],
    brief: BriefView,
) -> str:
    """Lo que lee la sesión del juez, como JSON (`SessionRequest.message`, 003; 012-C16): el
    título y los 10 capítulos tal como están, la story bible compacta, la rúbrica entera, el
    `CatalogoDeTropos` entero y, del brief, solo tono, género y deseos de trama. Nunca texto
    libre, cita de un hecho extraído, cronología, resúmenes, revisiones del editor, razonamiento
    del writer ni datos de otra novela o versión: no hay parámetro por el que pudieran entrar."""
    payload: dict[str, Any] = {
        "title": title,
        "chapters": [asdict(chapter) for chapter in chapters],
        "story_bible": _story_bible(story_bible),
        "rubric": [asdict(criterion) for criterion in NOVEL_RUBRIC],
        "trope_catalog": [asdict(trope) for trope in catalog],
        "brief": {"tone": brief.tone, "genre": brief.genre, "plot_wishes": list(brief.plot_wishes)},
    }
    return json.dumps(payload, ensure_ascii=False, default=str)


def _story_bible(bible: StoryBible) -> dict[str, Any]:
    return {
        "characters": [
            {"name": c.canonical_name, "facts": _facts(bible, character_id=c.id)}
            for c in bible.characters
        ],
        "places": [
            {"name": p.canonical_name, "facts": _facts(bible, place_id=p.id)} for p in bible.places
        ],
        "world": _facts(bible) if bible.world is not None else None,
    }


def _facts(
    bible: StoryBible, *, character_id: int | None = None, place_id: int | None = None
) -> list[dict[str, str]]:
    return [
        {"attribute": fact.attribute, "value": fact.value}
        for fact in bible.facts
        if fact.character_id == character_id and fact.place_id == place_id
    ]


# --- Agregación de la entrega (012-C13, 012-C14, 012-I5) ------------------------------------------


@dataclass(frozen=True)
class JudgeVerdict:
    passed: bool
    defects: tuple[Defect, ...]

    @property
    def score(self) -> float:
        return 1.0 if self.passed else 0.0


def judge_result(evaluation: JudgeEvaluation, thresholds: Mapping[str, int]) -> JudgeVerdict:
    """Agrega solo con campos estructurados: puntuación y capítulos citados, nunca el texto de
    ninguna justificación ni una media (012-I5). `juez-novela` depende solo de los tres criterios
    bloqueantes; ninguno compensa a otro (012-C13, 012-C14): un criterio bajo su umbral da un
    defecto por cada capítulo que cita, bloqueante solo si el criterio lo es."""
    defects = tuple(
        Defect(VALIDATOR, criterion.name, criterion.blocking, chapter, submission.justification)
        for criterion in NOVEL_RUBRIC
        for submission in (evaluation.get(criterion.name),)
        if submission.score < thresholds[criterion.name]
        for chapter in submission.chapters
    )
    passed = not any(defect.blocking for defect in defects)
    return JudgeVerdict(passed, defects)

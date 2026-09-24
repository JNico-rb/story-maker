"""`Rubrica` de novela: constante del dominio con los siete criterios del juez, tres bloqueantes
(`architecture.md` §11.3, `definitions.md`; 012-C25). Es la misma rúbrica que usa la revisión
humana (020). Sin I/O."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RubricCriterion:
    name: str
    blocking: bool


NOVEL_RUBRIC: tuple[RubricCriterion, ...] = (
    RubricCriterion("continuidad", True),
    RubricCriterion("coherencia-personajes", True),
    RubricCriterion("arco-y-final", True),
    RubricCriterion("ritmo", False),
    RubricCriterion("tono", False),
    RubricCriterion("personalizacion-natural", False),
    RubricCriterion("no-cliche", False),
)

"""Resultado de un validador del hook de validación de capítulo (`architecture.md` §7.5, §11.2)."""

from __future__ import annotations

from dataclasses import dataclass

from story_maker.agents.port import Defect


@dataclass(frozen=True)
class ChapterCheck:
    """Una ejecución de un validador sobre una entrega: pasa o no, el comentario de su score y
    sus defectos (bloqueantes)."""

    validator: str
    passed: bool
    comment: str
    defects: tuple[Defect, ...] = ()

    @property
    def score(self) -> int:
        return 1 if self.passed else 0

"""Precedencia entre resultados dentro de una pasada del `GateDePublicacion` (012-C17).

Combina lo que ya decidieron los validadores de la pasada (`validators/novel.py`,
`validators/judge.py`, y `cronologia-lean` de 007) en un único veredicto, sin volver a mirar
ningún resultado por dentro: lo no atribuible manda sobre la interrupción, y esta sobre lo
atribuible. Nada aquí abre una sesión, cuenta pasadas ni toca una candidata — eso, junto con las
etapas 3 y 4 y la reescritura en sí, es del gate completo, fuera de este paso (011 en otro
carril)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from story_maker.formal.defects import Defect

PassOutcome = Literal["fail", "interrupted", "rewrite", "continue"]


@dataclass(frozen=True)
class PassVerdict:
    outcome: PassOutcome
    reason: str | None = None
    chapters_to_rewrite: tuple[int, ...] = ()


def gate_precedence(
    *,
    unattributable_reason: str | None = None,
    interruption_reason: str | None = None,
    defects: tuple[Defect, ...] = (),
    judge_no_valid_delivery: bool = False,
    cycles_remaining: bool = True,
) -> PassVerdict:
    """El orden de 012-C17, sobre las etapas que corrieron en la pasada:

    1. Un fallo no atribuible (`unattributable_reason`) manda sobre todo lo demás.
    2. Si no hay ninguno, una interrupción (`interruption_reason`).
    3. Si no hay ninguna, los capítulos con algún defecto bloqueante atribuible, más el juez sin
       entrega válida (012-C15): reescritura si quedan ciclos, o `retries_exhausted` si no.
    4. Si no hay nada de lo anterior, la pasada sigue (a la etapa siguiente o a publicar)."""
    if unattributable_reason is not None:
        return PassVerdict("fail", unattributable_reason)
    if interruption_reason is not None:
        return PassVerdict("interrupted", interruption_reason)
    chapters = tuple(sorted({d.chapter for d in defects if d.blocking and d.chapter is not None}))
    if chapters or judge_no_valid_delivery:
        if cycles_remaining:
            return PassVerdict("rewrite", chapters_to_rewrite=chapters)
        return PassVerdict("fail", "retries_exhausted")
    return PassVerdict("continue")

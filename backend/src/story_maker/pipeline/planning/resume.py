"""Qué hace la fase `planning` al relanzar una ejecución interrumpida (010-C24, 010-C25).

El canon del brief no se reescribe (ya está, de 010-C01): quien reanuda solo decide si hace
falta abrir el planner de nuevo. Con el punto de control 0 escrito, la planificación ya terminó
y no hay nada que retomar aquí (`architecture.md` §9.2) — reanudar en `writing` es 011."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from story_maker.store.models import Attempt, Checkpoint, ValidatorResult
from story_maker.validators.outline import OutlineDefect

PLAN_EVALUABLE = "plan"


@dataclass(frozen=True)
class PlanResumeState:
    next_attempt_number: int
    defects: tuple[OutlineDefect, ...]


def has_checkpoint_zero(session: Session, run_id: int) -> bool:
    """El plan ya está aplicado si y solo si existe el punto de control 0 (010-I5)."""
    return (
        session.scalars(select(Checkpoint).filter_by(run_id=run_id, chapter=0)).first() is not None
    )


def plan_resume_state(session: Session, run_id: int) -> PlanResumeState:
    """El intento con el que sigue el planner al relanzar (010-C24): el siguiente al último
    intento *cerrado* — el que cortó una caída nunca llegó a `attempts`, así que no cuenta —, con
    los defectos de su último `ResultadoDeValidador` de `outline`."""
    attempts = session.scalars(
        select(Attempt)
        .filter_by(run_id=run_id, evaluable=PLAN_EVALUABLE)
        .order_by(Attempt.number.desc())
    ).first()
    if attempts is None:
        return PlanResumeState(1, ())
    result = session.scalars(
        select(ValidatorResult)
        .filter_by(run_id=run_id, validator="outline")
        .order_by(ValidatorResult.id.desc())
    ).first()
    defects = (
        tuple(
            OutlineDefect(d["message"], d["chapter"])
            for d in cast("list[dict[str, Any]]", result.detail)
        )
        if result is not None
        else ()
    )
    return PlanResumeState(attempts.number + 1, defects)

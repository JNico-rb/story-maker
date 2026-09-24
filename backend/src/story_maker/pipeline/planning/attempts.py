"""Intentos del evaluable `plan`: interpreta el resultado de una sesión del planner y lo deja
en `attempts` (010-C18, 010-C26, 010-C29).

Abrir la sesión siguiente con los defectos, aplicar el plan aceptado y descartar la candidata
tras agotar los intentos son las partes de la 010 que esperan a la story bible de 009 (canon
del brief, `discard()` de la versión) — ver `TODO.md` bloque 010. Aquí solo se interpreta el
`SessionResult` que ya da el puerto de agente (003) y se registra el intento."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

from story_maker.agents.port import SessionResult
from story_maker.pipeline.planning.plan import PlanSubmission
from story_maker.pipeline.planning.story_bible_view import StoryBibleView
from story_maker.store.models import Attempt, Run
from story_maker.store.session import UnitOfWork
from story_maker.validators.outline import OutlineDefect, judge_outline

Verdict = Literal["accept", "rewrite", "fail"]

PLAN_EVALUABLE = "plan"


@dataclass(frozen=True)
class PlanAttemptOutcome:
    verdict: Verdict
    defects: tuple[OutlineDefect, ...]
    plan: PlanSubmission | None


def judge_plan_delivery(
    result: SessionResult,
    *,
    story_bible: StoryBibleView,
    present_year: int,
    attempt_number: int,
    max_retries: int,
) -> PlanAttemptOutcome:
    """El veredicto de un intento del evaluable `plan` (`definitions.md` Veredicto): `accept`
    si `outline` no encuentra defectos; si no, `rewrite` mientras queden intentos y `fail` al
    agotarlos. Una sesión sin entrega válida (010-C18) es un intento fallido con un defecto de
    `schema-salida` que nombra el motivo — el desenlace de la sesión que dio el puerto."""
    deliveries = result.deliveries
    if deliveries:
        # La tool `submit_plan` solo valida contra `PlanSubmission` (`session.submit_plan_tool`).
        plan = cast(PlanSubmission, deliveries[-1].value)
        outline = judge_outline(plan, story_bible, present_year=present_year)
        if outline.passed:
            return PlanAttemptOutcome("accept", (), plan)
        defects = outline.defects
    else:
        plan = None
        defects = (OutlineDefect(f"sin entrega: {result.outcome}"),)
    verdict: Verdict = "rewrite" if attempt_number <= max_retries else "fail"
    return PlanAttemptOutcome(verdict, defects, plan)


def record_plan_attempt(uow: UnitOfWork, run: Run, number: int, verdict: Verdict) -> Attempt:
    """Un intento del evaluable `plan`, cerrado con su veredicto (`definitions.md` Intento)."""
    attempt = Attempt(
        run_id=run.id,
        evaluable=PLAN_EVALUABLE,
        chapter=None,
        gate_cycle=None,
        number=number,
        outcome=verdict,
    )
    uow.add(attempt)
    return attempt


def record_provider_failure(run: Run) -> None:
    """Fallo del proveedor (010-C26): la ejecución pasa a `interrupted` con `provider_error`; el
    intento abierto no se registra, así que no cuenta (`architecture.md` §7.6), y no se abre
    otra sesión. Quien llama decide cuándo confirmar la transacción."""
    run.status = "interrupted"
    run.reason = "provider_error"

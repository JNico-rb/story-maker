"""Intentos del evaluable `plan`: interpreta el resultado de una sesión del planner y lo deja
en `attempts`, y el juicio de `outline` en `validator_results` (010-C18, 010-C19, 010-C26,
010-C29).

Aplicar el plan aceptado a la story bible es 010-C20 (`pipeline/planning/phase.py`), aparte.
Aquí solo se interpreta el `SessionResult` que ya da el puerto de agente (003) y se registra
cada intento del evaluable `plan`."""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal, cast

from story_maker.agents.port import SessionResult, ToolCall
from story_maker.observability.port import ObservabilityPort, Trace
from story_maker.pipeline.planning.plan import PlanSubmission
from story_maker.pipeline.planning.session import SUBMIT_PLAN
from story_maker.pipeline.planning.story_bible_view import StoryBibleView
from story_maker.store.models import Attempt, Run, ValidatorResult
from story_maker.store.session import UnitOfWork
from story_maker.validators.outline import OutlineDefect, OutlineResult, judge_outline

OUTLINE_VALIDATOR = "outline"

Verdict = Literal["accept", "rewrite", "fail"]

PLAN_EVALUABLE = "plan"


@dataclass(frozen=True)
class PlanAttemptOutcome:
    verdict: Verdict
    defects: tuple[OutlineDefect, ...]
    plan: PlanSubmission | None
    attempt_number: int


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
            return PlanAttemptOutcome("accept", (), plan, attempt_number)
        defects = outline.defects
    else:
        plan = None
        defects = (OutlineDefect(f"sin entrega: {result.outcome}"),)
    verdict: Verdict = "rewrite" if attempt_number <= max_retries else "fail"
    return PlanAttemptOutcome(verdict, defects, plan, attempt_number)


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


def record_outline_result(
    uow: UnitOfWork,
    telemetry: ObservabilityPort,
    trace: Trace,
    run: Run,
    version_id: int,
    outline: OutlineResult,
) -> ValidatorResult:
    """El `ResultadoDeValidador` de un juicio de `outline`, con su span y su score en la traza
    de la ejecución (010-C29; `definitions.md` Score, `architecture.md` §13.1-§13.3)."""
    comment = "; ".join(d.message for d in outline.defects) or None
    with telemetry.span(trace, f"validador:{OUTLINE_VALIDATOR}") as span:
        telemetry.score(trace, OUTLINE_VALIDATOR, outline.score, comment=comment, span=span)
    row = ValidatorResult(
        run_id=run.id,
        version_id=version_id,
        validator=OUTLINE_VALIDATOR,
        chapter=None,
        passed=outline.passed,
        score=outline.score,
        detail=[{"message": d.message, "chapter": d.chapter} for d in outline.defects],
        created_at=dt.datetime.now(dt.UTC),
    )
    uow.add(row)
    return row


def cut_after_attempts(attempts_used_before: int, max_retries: int) -> Callable[[ToolCall], bool]:
    """`cut_when` de 003: cuando una entrega de `submit_plan` rechazada por schema o por policy
    agota los intentos que quedan, corta la sesión ahí mismo — el planner no llega a un intento
    de más (010-C19, segunda mitad)."""
    used = attempts_used_before

    def cut_when(call: ToolCall) -> bool:
        nonlocal used
        if call.tool != SUBMIT_PLAN or call.status not in ("schema_rejected", "denied"):
            return False
        used += 1
        return used >= 1 + max_retries

    return cut_when


def record_in_session_attempts(
    uow: UnitOfWork,
    run: Run,
    calls: Sequence[ToolCall],
    *,
    attempts_used_before: int,
    max_retries: int,
) -> Verdict | None:
    """Cada entrega de `submit_plan` que rechaza el schema o la policy dentro de una misma
    sesión es su propio intento del evaluable `plan` (010-C08, 010-C09, 010-C19): cuenta y se
    cierra con `rewrite`, o con `fail` si agota lo que quedaba. Da el veredicto del último
    intento registrado, o `None` si no hubo ninguna entrega rechazada."""
    verdict: Verdict | None = None
    count = attempts_used_before
    for call in calls:
        if call.tool != SUBMIT_PLAN or call.status not in ("schema_rejected", "denied"):
            continue
        count += 1
        verdict = "rewrite" if count <= max_retries else "fail"
        record_plan_attempt(uow, run, count, verdict)
    return verdict


def record_provider_failure(run: Run) -> None:
    """Fallo del proveedor (010-C26): la ejecución pasa a `interrupted` con `provider_error`; el
    intento abierto no se registra, así que no cuenta (`architecture.md` §7.6), y no se abre
    otra sesión. Quien llama decide cuándo confirmar la transacción."""
    run.status = "interrupted"
    run.reason = "provider_error"

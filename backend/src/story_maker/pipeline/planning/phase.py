"""Bucle de intentos de la fase `planning`: abre sesiones del planner hasta aceptar un plan o
agotar `max_retries.plan` (010-C17, 010-C29), y aplica el plan aceptado (010-C20, 010-C23).

Un plan `accept` no se registra en el bucle: su intento, su `ResultadoDeValidador` y la
aplicación entera se escriben en `finalize_accepted_plan`, una sola transacción — si la
aplicación falla, tampoco queda el intento (010-C23, «el intento aceptado queda sin desenlace y
no cuenta»)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable

from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import NeverFits
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.domain.trope_catalog import Trope
from story_maker.observability.port import ObservabilityPort, Trace
from story_maker.pipeline.planning.apply import apply_accepted_plan
from story_maker.pipeline.planning.attempts import (
    PlanAttemptOutcome,
    judge_plan_delivery,
    record_outline_result,
    record_plan_attempt,
    record_provider_failure,
)
from story_maker.pipeline.planning.brief_view import BriefView
from story_maker.pipeline.planning.story_bible_view import StoryBibleView
from story_maker.pipeline.planning.window import build_planner_window
from story_maker.store.models import Run
from story_maker.store.session import unit_of_work
from story_maker.store.versions import discard
from story_maker.validators.outline import OutlineDefect, OutlineResult


class ProviderFailure(Exception):
    """La sesión del planner terminó con `infrastructure_failure` (010-C26): la ejecución ya
    pasó a `interrupted`, el intento abierto no se registró y no se abre otra sesión."""


class InfeasibleConfig(Exception):
    """La reserva de la sesión del planner supera el `token_ceiling` (010-C27): no se abre
    ninguna sesión, no se cuenta ningún intento, y la ejecución ya terminó `failed` con
    `infeasible_config` con la candidata descartada."""


async def run_plan_phase(
    port: AgentPort,
    session_factory: sessionmaker[Session],
    telemetry: ObservabilityPort,
    trace: Trace,
    *,
    run_id: int,
    version_id: int,
    build_request: Callable[[str, int], SessionRequest],
    brief: BriefView,
    story_bible: StoryBibleView,
    catalog: tuple[Trope, ...],
    present_year: int,
    max_retries: int,
    now: dt.datetime,
    start_attempt_number: int = 1,
    initial_defects: tuple[OutlineDefect, ...] = (),
) -> PlanAttemptOutcome:
    """Una sesión del planner por intento, con la ventana de 010-C06 más los defectos del
    intento anterior, nunca el plan que rechazó (010-C17). Al relanzar (010-C24),
    `start_attempt_number` y `initial_defects` retoman donde cortó la caída, con
    `resume.resume_state`."""
    defects = initial_defects
    attempt_number = start_attempt_number
    while True:
        window = build_planner_window(brief, story_bible, catalog, defects=defects)
        try:
            result = await port.run(build_request(window, attempt_number))
        except NeverFits as exc:
            with unit_of_work(session_factory) as uow:
                run = _run(uow.session, run_id)
                run.status = "failed"
                run.reason = "infeasible_config"
                run.finished_at = now
                discard(uow, version_id)
            raise InfeasibleConfig(str(exc)) from exc
        if result.outcome == "infrastructure_failure":
            with unit_of_work(session_factory) as uow:
                record_provider_failure(_run(uow.session, run_id))
            raise ProviderFailure(f"intento {attempt_number}: {result.error}")
        outcome = judge_plan_delivery(
            result,
            story_bible=story_bible,
            present_year=present_year,
            attempt_number=attempt_number,
            max_retries=max_retries,
        )
        if outcome.verdict == "accept":
            # Su intento y su aplicación son una sola transacción (010-C23): ver
            # `finalize_accepted_plan`, que quien llama invoca aparte.
            return outcome
        with unit_of_work(session_factory) as uow:
            run = _run(uow.session, run_id)
            record_plan_attempt(uow, run, attempt_number, outcome.verdict)
            if outcome.plan is not None:
                outline_result = OutlineResult(passed=not outcome.defects, defects=outcome.defects)
                record_outline_result(uow, telemetry, trace, run, version_id, outline_result)
            if outcome.verdict == "fail":
                run.status = "failed"
                run.reason = "retries_exhausted"
                run.finished_at = now
                discard(uow, version_id)
        if outcome.verdict != "rewrite":
            return outcome
        defects = outcome.defects
        attempt_number += 1


def finalize_accepted_plan(
    session_factory: sessionmaker[Session],
    telemetry: ObservabilityPort,
    trace: Trace,
    run_id: int,
    version_id: int,
    outcome: PlanAttemptOutcome,
    *,
    now: dt.datetime,
) -> None:
    """El intento `accept`, su `ResultadoDeValidador` y la aplicación entera del plan, en una
    sola transacción (010-C20, 010-C23). Si algo falla a mitad, nada de eso queda: ni el
    intento, ni el mundo, ni el outline, ni el punto de control 0; la ejecución termina `failed`
    con `internal_error` y la candidata pasa a descartada, en una transacción aparte."""
    if outcome.verdict != "accept" or outcome.plan is None:
        raise ValueError("solo se aplica un plan aceptado")
    try:
        with unit_of_work(session_factory) as uow:
            run = _run(uow.session, run_id)
            record_plan_attempt(uow, run, outcome.attempt_number, "accept")
            record_outline_result(
                uow, telemetry, trace, run, version_id, OutlineResult(passed=True, defects=())
            )
            apply_accepted_plan(uow, run, version_id, outcome.plan, now=now)
    except Exception:
        with unit_of_work(session_factory) as uow:
            run = _run(uow.session, run_id)
            run.status = "failed"
            run.reason = "internal_error"
            run.finished_at = now
            discard(uow, version_id)
        raise


def _run(session: Session, run_id: int) -> Run:
    run = session.get(Run, run_id)
    if run is None:
        raise LookupError(f"no existe la ejecución {run_id}")
    return run

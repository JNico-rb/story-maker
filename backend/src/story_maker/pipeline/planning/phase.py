"""Bucle de intentos de la fase `planning`: abre sesiones del planner hasta aceptar un plan o
agotar `max_retries.plan` (010-C17, 010-C29).

Aplicar el plan aceptado a la story bible (010-C20), el punto de control 0 y el paso a
`writing` esperan a la 009 (`TODO.md` bloque 010): esta función llega hasta el veredicto
`accept` y lo devuelve; no lo aplica."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.domain.trope_catalog import Trope
from story_maker.observability.port import ObservabilityPort, Trace
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
from story_maker.validators.outline import OutlineDefect, OutlineResult


class ProviderFailure(Exception):
    """La sesión del planner terminó con `infrastructure_failure` (010-C26): la ejecución ya
    pasó a `interrupted`, el intento abierto no se registró y no se abre otra sesión."""


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
) -> PlanAttemptOutcome:
    """Una sesión del planner por intento, con la ventana de 010-C06 más los defectos del
    intento anterior, nunca el plan que rechazó (010-C17)."""
    defects: tuple[OutlineDefect, ...] = ()
    attempt_number = 1
    while True:
        window = build_planner_window(brief, story_bible, catalog, defects=defects)
        result = await port.run(build_request(window, attempt_number))
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
        with unit_of_work(session_factory) as uow:
            run = _run(uow.session, run_id)
            record_plan_attempt(uow, run, attempt_number, outcome.verdict)
            if outcome.plan is not None:
                outline_result = OutlineResult(passed=not outcome.defects, defects=outcome.defects)
                record_outline_result(uow, telemetry, trace, run, version_id, outline_result)
        if outcome.verdict != "rewrite":
            return outcome
        defects = outcome.defects
        attempt_number += 1


def _run(session: Session, run_id: int) -> Run:
    run = session.get(Run, run_id)
    if run is None:
        raise LookupError(f"no existe la ejecución {run_id}")
    return run

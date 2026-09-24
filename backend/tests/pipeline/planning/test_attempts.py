"""Intentos del evaluable `plan`: sesión sin entrega (010-C18) y fallo del proveedor
(010-C26). Abrir la sesión siguiente con los defectos, aplicar el plan y descartar la
candidata esperan a la story bible de 009 (ver el módulo `pipeline/planning/attempts.py`)."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from story_maker.agents.fake import Fail, FakeAgent, Say, Script
from story_maker.agents.port import AgentPort, SessionRequest, SessionResult
from story_maker.pipeline.planning.attempts import (
    judge_plan_delivery,
    record_plan_attempt,
    record_provider_failure,
)
from story_maker.pipeline.planning.story_bible_view import StoryBibleView
from story_maker.store.models import Attempt, Run
from story_maker.store.session import unit_of_work
from story_maker.validators.outline import OutlineDefect

STORY_BIBLE = StoryBibleView(present_year=2026)


def _result(outcome: str) -> SessionResult:
    return SessionResult(
        outcome=outcome,  # type: ignore[arg-type]
        calls=[],
        text=None,
        model="claude-sonnet-5",
        usage=None,
        cost_usd=None,
        sdk_cost_usd=None,
        latency_ms=0,
        reserved_tokens=0,
        role_session_id=1,
    )


@pytest.mark.parametrize("outcome", ["turns_exhausted", "time_exhausted", "completed"])
def test_a_session_that_ends_without_a_valid_delivery_names_the_reason(outcome: str) -> None:
    """010-C18: agota `max_turns`, agota `session_timeout_seconds`, o acaba sin llamarla
    (`completed` con cero entregas)."""
    outcome_result = judge_plan_delivery(
        _result(outcome),
        story_bible=STORY_BIBLE,
        present_year=2026,
        attempt_number=1,
        max_retries=2,
    )

    assert outcome_result.plan is None
    assert outcome_result.defects == (OutlineDefect(f"sin entrega: {outcome}"),)
    assert outcome_result.verdict == "rewrite"


def test_a_failed_attempt_without_delivery_follows_the_usual_verdict_rule() -> None:
    """Con el último intento disponible, la regla de siempre da `fail`, no `rewrite`."""
    outcome_result = judge_plan_delivery(
        _result("completed"),
        story_bible=STORY_BIBLE,
        present_year=2026,
        attempt_number=3,
        max_retries=2,
    )

    assert outcome_result.verdict == "fail"


async def test_a_session_without_delivery_is_recorded_as_a_failed_attempt(
    port: AgentPort,
    fake: FakeAgent,
    session_factory: sessionmaker,  # type: ignore[type-arg]
    run_id: int,
    plan_request: SessionRequest,
) -> None:
    fake.script("planner", "plan", Script(steps=(Say("No sé qué proponer."),)))

    result = await port.run(plan_request)
    outcome = judge_plan_delivery(
        result, story_bible=STORY_BIBLE, present_year=2026, attempt_number=1, max_retries=2
    )
    with unit_of_work(session_factory) as uow:
        run = uow.session.get(Run, run_id)
        assert run is not None
        record_plan_attempt(uow, run, 1, outcome.verdict)

    with session_factory() as session:
        (attempt,) = session.scalars(select(Attempt)).all()
    fields = (attempt.evaluable, attempt.chapter, attempt.number, attempt.outcome, attempt.run_id)
    assert fields == ("plan", None, 1, "rewrite", run_id)


async def test_a_provider_failure_interrupts_the_run_without_counting_an_attempt(
    port: AgentPort,
    fake: FakeAgent,
    session_factory: sessionmaker,  # type: ignore[type-arg]
    run_id: int,
    plan_request: SessionRequest,
) -> None:
    fake.script("planner", "plan", Script(steps=(Fail(result=True),)))

    result = await port.run(plan_request)

    assert result.outcome == "infrastructure_failure"
    assert len(fake.sessions) == 1

    with unit_of_work(session_factory) as uow:
        run = uow.session.get(Run, run_id)
        assert run is not None
        record_provider_failure(run)

    with session_factory() as session:
        run = session.get(Run, run_id)
        assert run is not None
        assert (run.status, run.reason) == ("interrupted", "provider_error")
        assert session.scalars(select(Attempt)).all() == []

"""Replanificación con los defectos (010-C17) y resultado y score de `outline` (010-C29).

Esta prueba llega hasta la aplicación del plan aceptado (010-C20), con `finalize_accepted_plan`
(`pipeline/planning/phase.py`)."""

from __future__ import annotations

import datetime as dt
import json

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.planning.test_candidate import reference_brief
from tests.validators.test_outline import STORY_BIBLE, reference_plan

from story_maker.agents.fake import Call, FakeAgent, Say, Script
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.domain.trope_catalog import TROPE_CATALOG
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Trace
from story_maker.pipeline.planning.brief_view import BriefView, RecipientView
from story_maker.pipeline.planning.candidate import start_generation_phase
from story_maker.pipeline.planning.phase import finalize_accepted_plan, run_plan_phase
from story_maker.pipeline.planning.session import submit_plan_tool
from story_maker.store.models import Attempt, Checkpoint, RoleSession, Run, ValidatorResult

BRIEF = BriefView(recipient=RecipientView(name="Marta", age=40))
NOW = dt.datetime(2026, 9, 24, 12, 0)

NINE_CHAPTER_PLAN = json.loads(reference_plan().model_dump_json())
NINE_CHAPTER_PLAN["chapters"] = NINE_CHAPTER_PLAN["chapters"][:9]
REFERENCE_PLAN = json.loads(reference_plan().model_dump_json())


@pytest.fixture
def trace() -> Trace:
    return Trace(key="run:1")


async def test_a_rejected_plan_is_retried_with_its_defects_and_the_second_attempt_is_accepted(
    port: AgentPort,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    telemetry: NullObservability,
    trace: Trace,
    run_id: int,
    user_id: int,
    novel_id: int,
) -> None:
    version = start_generation_phase(session_factory, run_id, novel_id, reference_brief(), now=NOW)
    candidate_version_id = version.id
    fake.script(
        "planner",
        "plan",
        Script(steps=(Call("submit_plan", NINE_CHAPTER_PLAN), Say("Ahí va."))),
    )
    fake.script(
        "planner",
        "plan",
        Script(steps=(Call("submit_plan", REFERENCE_PLAN), Say("Ahí va."))),
    )

    def build_request(message: str, attempt_number: int) -> SessionRequest:
        return SessionRequest(
            role="planner",
            mode="plan",
            user_id=user_id,
            novel_id=novel_id,
            run_id=run_id,
            prompt="Prompt del planner",
            prompt_version="v1",
            message=message,
            tools=(submit_plan_tool(),),
            trace=trace,
        )

    outcome = await run_plan_phase(
        port,
        session_factory,
        telemetry,
        trace,
        run_id=run_id,
        version_id=candidate_version_id,
        build_request=build_request,
        brief=BRIEF,
        story_bible=STORY_BIBLE,
        catalog=TROPE_CATALOG,
        present_year=2026,
        max_retries=2,
        now=NOW,
    )

    assert outcome.verdict == "accept"
    assert len(fake.sessions) == 2

    second_window = fake.sessions[1].request.message
    assert "9 capítulos" in second_window
    assert "El verano de Marta" not in second_window  # el plan rechazado no vuelve a entrar

    finalize_accepted_plan(
        session_factory, telemetry, trace, run_id, candidate_version_id, outcome, now=NOW
    )

    with session_factory() as session:
        attempts = session.scalars(select(Attempt).order_by(Attempt.number)).all()
        assert [(a.number, a.outcome) for a in attempts] == [(1, "rewrite"), (2, "accept")]

        results = session.scalars(select(ValidatorResult).order_by(ValidatorResult.id)).all()
        assert [(r.validator, r.passed, r.score) for r in results] == [
            ("outline", False, 0.0),
            ("outline", True, 1.0),
        ]

        role_sessions = session.scalars(select(RoleSession)).all()
        assert len(role_sessions) == 2

        run = session.get(Run, run_id)
        assert run is not None
        assert run.phase == "writing"
        (checkpoint,) = session.scalars(select(Checkpoint).filter_by(run_id=run_id)).all()
        assert checkpoint.chapter == 0

    scores = [s for s in trace.scores if s.name == "outline"]
    assert [s.value for s in scores] == [0, 1]
    assert "9 capítulos" in (scores[0].comment or "")
    assert scores[0].span is not None
    assert scores[0].span.name == "validador:outline"

    # Cada sesión del planner deja su span `rol:planner` y, dentro, `tool:submit_plan` (003).
    role_spans = [span for span in trace.spans if span.name == "rol:planner"]
    assert len(role_spans) == 2
    assert all(any(c.name == "tool:submit_plan" for c in span.children) for span in role_spans)

"""Intentos agotados (010-C19): tres sesiones rechazadas por `outline` agotan `max_retries.plan`
y la candidata se descarta."""

from __future__ import annotations

import datetime as dt
import json

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from tests.validators.test_outline import STORY_BIBLE, reference_plan

from story_maker.agents.fake import Call, FakeAgent, Say, Script
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.domain.trope_catalog import TROPE_CATALOG
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Trace
from story_maker.pipeline.planning.brief_view import BriefView, RecipientView
from story_maker.pipeline.planning.phase import run_plan_phase
from story_maker.pipeline.planning.session import submit_plan_tool
from story_maker.store.models import Attempt, Run, Version

BRIEF = BriefView(recipient=RecipientView(name="Marta", age=40))
NINE_CHAPTER_PLAN = json.loads(reference_plan().model_dump_json())
NINE_CHAPTER_PLAN["chapters"] = NINE_CHAPTER_PLAN["chapters"][:9]


async def test_three_rejected_plans_exhaust_the_retries_and_discard_the_candidate(
    port: AgentPort,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    telemetry: NullObservability,
    run_id: int,
    user_id: int,
    novel_id: int,
    candidate_version_id: int,
) -> None:
    trace = Trace(key="run:1")
    for _ in range(3):
        fake.script(
            "planner", "plan", Script(steps=(Call("submit_plan", NINE_CHAPTER_PLAN), Say("Va.")))
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
        now=dt.datetime(2026, 9, 24, 12, 0),
    )

    assert outcome.verdict == "fail"
    assert len(fake.sessions) == 3

    with session_factory() as session:
        attempts = session.scalars(select(Attempt).order_by(Attempt.number)).all()
        assert [(a.number, a.outcome) for a in attempts] == [
            (1, "rewrite"),
            (2, "rewrite"),
            (3, "fail"),
        ]

        run = session.get(Run, run_id)
        assert run is not None
        assert (run.status, run.reason) == ("failed", "retries_exhausted")

        version = session.get(Version, candidate_version_id)
        assert version is not None
        assert version.status == "discarded"

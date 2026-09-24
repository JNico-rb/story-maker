"""Relanzar antes del punto de control 0 (010-C24) y tras él (010-C25)."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.planning.test_candidate import reference_brief
from tests.validators.test_outline import STORY_BIBLE, reference_plan

from story_maker.agents.fake import Call, FakeAgent, Say, Script
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.domain.trope_catalog import TROPE_CATALOG
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Trace
from story_maker.pipeline.planning.attempts import PlanAttemptOutcome
from story_maker.pipeline.planning.brief_view import BriefView, RecipientView
from story_maker.pipeline.planning.candidate import start_generation_phase
from story_maker.pipeline.planning.phase import finalize_accepted_plan, run_plan_phase
from story_maker.pipeline.planning.resume import has_checkpoint_zero, plan_resume_state
from story_maker.pipeline.planning.session import submit_plan_tool
from story_maker.store.models import Attempt, Character, Checkpoint, ValidatorResult
from story_maker.store.session import unit_of_work

BRIEF = BriefView(recipient=RecipientView(name="Marta", age=40))
NOW = dt.datetime(2026, 9, 24, 12, 0)


async def test_relaunching_before_checkpoint_zero_resumes_the_next_attempt_with_its_defects(
    port: AgentPort,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    telemetry: NullObservability,
    run_id: int,
    user_id: int,
    novel_id: int,
) -> None:
    version = start_generation_phase(session_factory, run_id, novel_id, reference_brief(), now=NOW)
    with session_factory() as session:
        before_characters = sorted(
            c.canonical_name
            for c in session.scalars(select(Character).filter_by(version_id=version.id))
        )

    # El intento 1 cerró `rewrite`; el intento 2 estaba abierto cuando cayó: nunca se registró.
    with unit_of_work(session_factory) as uow:
        uow.add(Attempt(run_id=run_id, evaluable="plan", chapter=None, number=1, outcome="rewrite"))
        uow.add(
            ValidatorResult(
                run_id=run_id,
                version_id=version.id,
                validator="outline",
                chapter=None,
                passed=False,
                score=0.0,
                detail=[{"message": "la novela tiene 9 capítulos; se esperan 10", "chapter": None}],
                created_at=NOW,
            )
        )

    with session_factory() as session:
        assert not has_checkpoint_zero(session, run_id)
        state = plan_resume_state(session, run_id)
    assert state.next_attempt_number == 2
    assert [d.message for d in state.defects] == ["la novela tiene 9 capítulos; se esperan 10"]

    reference_payload = reference_plan().model_dump(mode="json")
    fake.script(
        "planner", "plan", Script(steps=(Call("submit_plan", reference_payload), Say("Va.")))
    )
    trace = Trace(key="run:1")

    def build_request(message: str, attempt_number: int) -> SessionRequest:
        assert "9 capítulos" in message  # los defectos del intento 1 entran en la ventana
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
        version_id=version.id,
        build_request=build_request,
        brief=BRIEF,
        story_bible=STORY_BIBLE,
        catalog=TROPE_CATALOG,
        present_year=2026,
        max_retries=2,
        now=NOW,
        start_attempt_number=state.next_attempt_number,
        initial_defects=state.defects,
    )

    assert outcome.verdict == "accept"
    assert outcome.attempt_number == 2  # el intento 3 seguiría cabiendo si hiciera falta
    assert len(fake.sessions) == 1  # una sola sesión nueva, no repite la 1

    with session_factory() as session:
        after_characters = sorted(
            c.canonical_name for c in session.query(Character).filter_by(version_id=version.id)
        )
    assert after_characters == before_characters  # el canon del brief no se reescribe


async def test_relaunching_after_checkpoint_zero_does_not_reopen_the_planner(
    session_factory: sessionmaker[Session], run_id: int, novel_id: int
) -> None:
    """Con el punto de control 0 ya escrito, quien reanude no abre el planner ni cuenta un
    intento del plan (010-C25): esta prueba solo cubre la detección de la que depende esa
    decisión — orquestar la reanudación en `writing` es 011."""
    version = start_generation_phase(session_factory, run_id, novel_id, reference_brief(), now=NOW)
    assert not has_checkpoint_zero(session_factory(), run_id)

    outcome = PlanAttemptOutcome("accept", (), reference_plan(), attempt_number=1)
    finalize_accepted_plan(
        session_factory,
        NullObservability(),
        Trace(key="run:1"),
        run_id,
        version.id,
        outcome,
        now=NOW,
    )

    assert has_checkpoint_zero(session_factory(), run_id)
    with session_factory() as session:
        checkpoints = session.scalars(select(Checkpoint).filter_by(run_id=run_id)).all()
        attempts = session.scalars(select(Attempt).filter_by(run_id=run_id, evaluable="plan")).all()
    assert [c.chapter for c in checkpoints] == [0]
    assert [a.outcome for a in attempts] == ["accept"]

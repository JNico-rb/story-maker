"""010-I2: planificar no modifica ni borra nada de origen brief o `free_text`. El canon escrito
al arrancar la fase (`_brief_origin_fingerprint`, `test_apply.py`) sigue idéntico tras un intento
rechazado (010-C17), tras aplicar el plan aceptado (010-C20, ya cubierto en `test_apply.py`) y
tras relanzar antes del punto de control 0 (010-C24)."""

from __future__ import annotations

import datetime as dt
import json

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.planning.test_apply import _brief_origin_fingerprint
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
from story_maker.pipeline.planning.resume import has_checkpoint_zero, plan_resume_state
from story_maker.pipeline.planning.session import submit_plan_tool
from story_maker.store.models import Attempt, ValidatorResult
from story_maker.store.session import unit_of_work

BRIEF = BriefView(recipient=RecipientView(name="Marta", age=40))
NOW = dt.datetime(2026, 9, 24, 12, 0)


async def test_the_brief_canon_is_unchanged_after_a_rejected_attempt_is_retried(
    port: AgentPort,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    telemetry: NullObservability,
    run_id: int,
    user_id: int,
    novel_id: int,
) -> None:
    version = start_generation_phase(session_factory, run_id, novel_id, reference_brief(), now=NOW)
    before = _brief_origin_fingerprint(session_factory, version.id)

    nine_chapter_plan = json.loads(reference_plan().model_dump_json())
    nine_chapter_plan["chapters"] = nine_chapter_plan["chapters"][:9]
    fake.script(
        "planner", "plan", Script(steps=(Call("submit_plan", nine_chapter_plan), Say("Ahí va.")))
    )
    trace = Trace(key="run:1")

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
        version_id=version.id,
        build_request=build_request,
        brief=BRIEF,
        story_bible=STORY_BIBLE,
        catalog=TROPE_CATALOG,
        present_year=2026,
        max_retries=0,
        now=NOW,
    )

    assert outcome.verdict == "fail"  # sin más intentos, pero el canon de origen no se toca
    assert _brief_origin_fingerprint(session_factory, version.id) == before


async def test_the_brief_canon_is_unchanged_after_relaunching_and_applying_the_plan(
    port: AgentPort,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    telemetry: NullObservability,
    run_id: int,
    user_id: int,
    novel_id: int,
) -> None:
    version = start_generation_phase(session_factory, run_id, novel_id, reference_brief(), now=NOW)
    before = _brief_origin_fingerprint(session_factory, version.id)

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

    fake.script(
        "planner",
        "plan",
        Script(steps=(Call("submit_plan", reference_plan().model_dump(mode="json")), Say("Va."))),
    )
    trace = Trace(key="run:1")

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
    assert _brief_origin_fingerprint(session_factory, version.id) == before

    finalize_accepted_plan(
        session_factory, telemetry, trace, run_id, version.id, outcome, now=NOW
    )
    assert _brief_origin_fingerprint(session_factory, version.id) == before

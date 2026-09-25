"""010-I1: ninguna ventana del planner contiene el contenido de un `TextoLibre` ni la cita de un
`HechoExtraido`; de un hecho aceptado solo llegan sujeto, atributo y valor.

`test_window.py` ya lo prueba a nivel de `build_planner_window` (010-C06). Aquí se comprueba
sobre las ventanas que de verdad captura el doble falso al atravesar el bucle de intentos
(010-C17, replanificar con defectos) y al relanzar antes del punto de control 0 (010-C24):
ninguna de las dos vías tiene otro parámetro por el que colar texto libre o la cita de un hecho,
pero la garantía solo vale si se mira lo que sale de `port.run`, no solo la función que arma la
ventana."""

from __future__ import annotations

import datetime as dt
import json

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.planning.test_candidate import reference_brief
from tests.validators.test_outline import STORY_BIBLE, reference_plan

from story_maker.agents.fake import Call, FakeAgent, Say, Script
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.domain.trope_catalog import TROPE_CATALOG
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Trace
from story_maker.pipeline.planning.attempts import PlanAttemptOutcome
from story_maker.pipeline.planning.brief_view import BriefView, ExtractedFactView, RecipientView
from story_maker.pipeline.planning.candidate import start_generation_phase
from story_maker.pipeline.planning.phase import run_plan_phase
from story_maker.pipeline.planning.resume import has_checkpoint_zero, plan_resume_state
from story_maker.pipeline.planning.session import submit_plan_tool
from story_maker.store.models import Attempt, ValidatorResult
from story_maker.store.session import unit_of_work

NOW = dt.datetime(2026, 9, 24, 12, 0)

FREE_TEXT_MARKER = (
    "el verano de las gaviotas azules"  # texto libre de la entrevista, nunca confirmado
)
EXTRACTED_QUOTE_MARKER = "cita original: dijo que colecciona conchas de pequeña"

BRIEF = BriefView(
    recipient=RecipientView(name="Marta", age=40),
    accepted_extracted_facts=(ExtractedFactView("Marta", "hobby", "Marta colecciona conchas"),),
)


def _assert_window_excludes_source_text(message: str) -> None:
    assert FREE_TEXT_MARKER not in message
    assert EXTRACTED_QUOTE_MARKER not in message
    payload = json.loads(message)
    (fact,) = payload["brief"]["accepted_extracted_facts"]
    assert set(fact) == {"subject", "attribute", "value"}


async def test_the_replanning_window_never_carries_free_text_or_a_fact_quote(
    port: AgentPort,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    telemetry: NullObservability,
    run_id: int,
    user_id: int,
    novel_id: int,
) -> None:
    version = start_generation_phase(session_factory, run_id, novel_id, reference_brief(), now=NOW)
    nine_chapter_plan = json.loads(reference_plan().model_dump_json())
    nine_chapter_plan["chapters"] = nine_chapter_plan["chapters"][:9]
    fake.script(
        "planner", "plan", Script(steps=(Call("submit_plan", nine_chapter_plan), Say("Ahí va.")))
    )
    fake.script(
        "planner",
        "plan",
        Script(
            steps=(Call("submit_plan", json.loads(reference_plan().model_dump_json())), Say("Va."))
        ),
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
    )

    assert outcome.verdict == "accept"
    assert len(fake.sessions) == 2  # el intento 1 rechazado y el intento 2 replanificado
    for recorded_session in fake.sessions:
        _assert_window_excludes_source_text(recorded_session.request.message)


async def test_the_resumed_window_never_carries_free_text_or_a_fact_quote(
    port: AgentPort,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    telemetry: NullObservability,
    run_id: int,
    user_id: int,
    novel_id: int,
) -> None:
    version = start_generation_phase(session_factory, run_id, novel_id, reference_brief(), now=NOW)
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
    assert len(fake.sessions) == 1
    _assert_window_excludes_source_text(fake.sessions[0].request.message)


def test_relaunching_after_checkpoint_zero_never_opens_a_planner_window(
    session_factory: sessionmaker[Session], run_id: int, novel_id: int
) -> None:
    """Con el punto de control 0 ya escrito, no hay ventana que construir: la reanudación no
    vuelve a abrir el planner (010-C25), así que no hay nada que verificar sobre su contenido."""
    version = start_generation_phase(session_factory, run_id, novel_id, reference_brief(), now=NOW)
    outcome = PlanAttemptOutcome("accept", (), reference_plan(), attempt_number=1)
    from story_maker.pipeline.planning.phase import finalize_accepted_plan

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

"""010-C19, segunda mitad: con `max_retries.plan` = 1, una entrega fuera de schema y luego una
denegada por policy, en la misma sesión, agotan los dos intentos disponibles. La segunda
denegación cierra el último intento con `fail` y corta la sesión: el planner no llega a un
tercer intento (`architecture.md` §7.6, `SessionRequest.cut_when` de 003)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.planning.conftest import ban

from story_maker.agents.fake import Call, FakeAgent, Say, Script
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.pipeline.planning.attempts import cut_after_attempts, record_in_session_attempts
from story_maker.store.models import Attempt, Run
from story_maker.store.session import unit_of_work


async def test_a_schema_rejection_and_a_banned_term_denial_exhaust_the_budget_in_one_session(
    port: AgentPort,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    novel_id: int,
    run_id: int,
    plan_request: SessionRequest,
) -> None:
    ban(session_factory, level="novel", term="Julián", novel_id=novel_id)
    plan_with_julian = {
        "world": {
            "novum_description": "Las IA razonan.",
            "novum_scope": "technological",
            "novum_date": "2021-05-01",
            "consequences": ["Una.", "Dos."],
        },
        "chapters": [],
        "style_sheet": {"narrator": "third", "tense": "past", "default_treatment": "tu"},
        "title": "La novela de Julián",
    }
    fake.script(
        "planner",
        "plan",
        Script(
            steps=(
                Call("submit_plan", {}),
                Call("submit_plan", plan_with_julian),
                Say("¿Otra vez?"),
            )
        ),
    )
    cut_when = cut_after_attempts(attempts_used_before=0, max_retries=1)
    request = SessionRequest(
        role=plan_request.role,
        mode=plan_request.mode,
        user_id=plan_request.user_id,
        novel_id=plan_request.novel_id,
        run_id=run_id,
        prompt=plan_request.prompt,
        prompt_version=plan_request.prompt_version,
        message=plan_request.message,
        tools=plan_request.tools,
        trace=plan_request.trace,
        cut_when=cut_when,
    )

    result = await port.run(request)

    assert result.outcome == "cut"
    assert [c.status for c in result.calls] == ["schema_rejected", "denied"]

    with unit_of_work(session_factory) as uow:
        run = uow.session.get(Run, run_id)
        assert run is not None
        verdict = record_in_session_attempts(
            uow, run, result.calls, attempts_used_before=0, max_retries=1
        )

    assert verdict == "fail"
    with session_factory() as session:
        attempts = session.scalars(select(Attempt).order_by(Attempt.number)).all()
        assert [(a.number, a.outcome) for a in attempts] == [(1, "rewrite"), (2, "fail")]

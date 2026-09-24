"""Reserva inviable en el techo (010-C27): un `token_ceiling` de prueba menor que la reserva de
la sesión del planner no abre ninguna sesión ni cuenta ningún intento."""

from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.planning.test_candidate import reference_brief
from tests.validators.test_outline import STORY_BIBLE

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import FakeAgent, Say, Script
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.config import Config
from story_maker.domain.trope_catalog import TROPE_CATALOG
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Trace
from story_maker.pipeline.planning.brief_view import BriefView, RecipientView
from story_maker.pipeline.planning.candidate import start_generation_phase
from story_maker.pipeline.planning.phase import InfeasibleConfig, run_plan_phase
from story_maker.pipeline.planning.session import BannedTermsPolicy, submit_plan_tool
from story_maker.store.models import Attempt, Run, Version

BRIEF = BriefView(recipient=RecipientView(name="Marta", age=40))
NOW = dt.datetime(2026, 9, 24, 12, 0)


@pytest.fixture
def tiny_ceiling(config: Config) -> TokenCeiling:
    return TokenCeiling(1)  # ninguna reserva real cabe en 1 token


@pytest.fixture
def port_with_tiny_ceiling(
    fake: FakeAgent,
    config: Config,
    tiny_ceiling: TokenCeiling,
    session_factory: sessionmaker[Session],
    telemetry: NullObservability,
    workspace: object,
) -> AgentPort:
    return AgentPort(
        agent=fake,
        config=config,
        ceiling=tiny_ceiling,
        policy=BannedTermsPolicy(session_factory),
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace,  # type: ignore[arg-type]
    )


async def test_a_reservation_that_never_fits_fails_the_run_without_opening_a_session(
    port_with_tiny_ceiling: AgentPort,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    telemetry: NullObservability,
    run_id: int,
    user_id: int,
    novel_id: int,
) -> None:
    version = start_generation_phase(session_factory, run_id, novel_id, reference_brief(), now=NOW)
    fake.script("planner", "plan", Script(steps=(Say("no debería leerse"),)))
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

    with pytest.raises(InfeasibleConfig):
        await run_plan_phase(
            port_with_tiny_ceiling,
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

    assert fake.sessions == []
    with session_factory() as session:
        assert session.scalars(select(Attempt)).all() == []
        run = session.get(Run, run_id)
        assert run is not None
        assert (run.status, run.reason) == ("failed", "infeasible_config")
        candidate = session.get(Version, version.id)
        assert candidate is not None
        assert candidate.status == "discarded"

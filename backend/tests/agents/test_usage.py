"""Uso, coste y registro de cada sesión (003-C25, I5, C26, C27)."""

from __future__ import annotations

import asyncio
import dataclasses
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import NeverFits, NoRoomInTime, TokenCeiling
from story_maker.agents.fake import Call, Fail, FakeAgent, Hang, Say, Script
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.agents.profiles import ToolsMismatch
from story_maker.agents.tools import ToolSpec
from story_maker.agents.usage import Usage, cost_usd
from story_maker.config import Config, PriceConfig
from story_maker.observability.null import NullObservability
from story_maker.store.models import RoleSession

LIST_PRICE = PriceConfig(input=2.00, output=10.00, cache_read=0.20, cache_write=2.50)


def priced(config: Config, model: str, price: PriceConfig) -> Config:
    roles = dict(config.roles)
    roles["writer"] = dataclasses.replace(roles["writer"], model=model)
    return dataclasses.replace(config, roles=roles, pricing={**config.pricing, model: price})


def build_port(
    config: Config,
    fake: FakeAgent,
    policy: Any,
    telemetry: NullObservability,
    session_factory: sessionmaker[Session],
    workspace: Path,
) -> AgentPort:
    return AgentPort(
        agent=fake,
        config=config,
        ceiling=TokenCeiling(config.token_ceiling),
        policy=policy,
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace,
    )


async def test_the_cost_is_the_real_usage_times_the_list_price_of_the_model(
    config: Config,
    fake: FakeAgent,
    policy: Any,
    telemetry: NullObservability,
    session_factory: sessionmaker[Session],
    workspace: Path,
    make_request: Callable[..., SessionRequest],
) -> None:
    usage = Usage(
        input_tokens=10_000, output_tokens=3_000, cache_read_tokens=50_000, cache_write_tokens=8_000
    )
    fake.script("writer", "write", Script(steps=(Say("fin"),), usage=usage, sdk_cost_usd=20.0))
    port = build_port(
        priced(config, "claude-sonnet-5", LIST_PRICE),
        fake,
        policy,
        telemetry,
        session_factory,
        workspace,
    )
    request = make_request("writer", "write")

    result = await port.run(request)

    # (10.000·2,00 + 3.000·10,00 + 50.000·0,20 + 8.000·2,50) / 1.000.000
    assert result.cost_usd == pytest.approx(0.08)
    (role_span,) = request.trace.spans
    (model_call,) = role_span.model_calls
    assert model_call.cost_usd == pytest.approx(0.08)
    with session_factory() as session:
        row = session.get(RoleSession, result.role_session_id)
        assert row is not None
        assert row.cost_usd == pytest.approx(0.08)
        # el coste del SDK solo queda como contraste
        assert row.sdk_cost_usd == 20.0
    assert result.sdk_cost_usd == 20.0


TOKENS = st.integers(min_value=0, max_value=2_000_000)


@settings(
    max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    usage=st.builds(Usage, TOKENS, TOKENS, TOKENS, TOKENS),
    sdk_cost=st.one_of(st.none(), st.floats(min_value=0, max_value=1_000, allow_nan=False)),
)
def test_the_role_session_cost_is_usage_times_pricing_never_the_sdk_one(
    usage: Usage,
    sdk_cost: float | None,
    config: Config,
    policy: Any,
    session_factory: sessionmaker[Session],
    workspace: Path,
    make_request: Callable[..., SessionRequest],
) -> None:
    fake = FakeAgent()
    fake.script("judge", None, Script(steps=(Say("nota"),), usage=usage, sdk_cost_usd=sdk_cost))
    port = build_port(config, fake, policy, NullObservability(), session_factory, workspace)

    result = asyncio.run(port.run(make_request("judge")))

    price = config.pricing[config.roles["judge"].model]
    with session_factory() as session:
        row = session.get(RoleSession, result.role_session_id)
        assert row is not None
        assert row.cost_usd == pytest.approx(cost_usd(usage, price))
        assert row.sdk_cost_usd == sdk_cost


CHAPTER = {"title": "Uno", "text": "limpio"}
USAGE = Usage(input_tokens=120, output_tokens=80, cache_read_tokens=30, cache_write_tokens=10)
BY_OUTCOME = {
    "completed": Script(steps=(Say("fin"),), usage=USAGE),
    "turns_exhausted": Script(steps=(Call("submit_chapter", CHAPTER),) * 9, usage=USAGE),
    "time_exhausted": Script(steps=(Hang(),), usage=USAGE),
    "cut": Script(steps=(Call("submit_chapter", CHAPTER), Say("fin")), usage=USAGE),
    "infrastructure_failure": Script(steps=(Fail(result=True),), usage=USAGE),
}


async def test_every_opened_session_leaves_its_role_session_and_only_they_do(
    config: Config,
    fake: FakeAgent,
    policy: Any,
    telemetry: NullObservability,
    session_factory: sessionmaker[Session],
    workspace: Path,
    novel_id: int,
    run_id: int,
    make_request: Callable[..., SessionRequest],
    tool_named: Callable[..., ToolSpec],
) -> None:
    tuned = dataclasses.replace(config, session_timeout_seconds=1, api_wait_seconds=1)
    ceiling = TokenCeiling(tuned.token_ceiling)
    port = AgentPort(
        agent=fake,
        config=tuned,
        ceiling=ceiling,
        policy=policy,
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace,
    )
    for outcome, script in BY_OUTCOME.items():
        fake.script("writer", "write", script)
        cut_when = (lambda call: True) if outcome == "cut" else None
        result = await port.run(
            make_request("writer", "write", run_id=run_id, chapter=4, cut_when=cut_when)
        )
        assert result.outcome == outcome
    fake.script(
        "interviewer",
        None,
        Script(steps=(Call("update_brief", {"field": "tone", "value": "funny"}),), usage=USAGE),
    )
    await port.run(make_request("interviewer"))  # quien la abrió descarta la entrega

    with pytest.raises(ToolsMismatch):
        await port.run(make_request("editor", tools=(tool_named("submit_chapter"),)))
    fake.script("judge", None, Script(steps=(Say("nota"),), usage=USAGE))
    blocker = await ceiling.acquire(ceiling.limit, None)
    with pytest.raises(NoRoomInTime):
        await port.run(make_request("judge"))
    ceiling.release(blocker)
    with pytest.raises(NeverFits):
        await port.run(make_request("judge", message="m" * 4 * (ceiling.limit + 1)))

    with session_factory() as session:
        rows = session.scalars(select(RoleSession).order_by(RoleSession.id)).all()
    assert [(r.role, r.outcome) for r in rows] == [
        *(("writer", outcome) for outcome in BY_OUTCOME),
        ("interviewer", "completed"),
    ]
    writer, interviewer = rows[0], rows[-1]
    assert (writer.novel_id, writer.run_id, writer.chapter) == (novel_id, run_id, 4)
    assert writer.model == tuned.roles["writer"].model
    assert writer.prompt_version == "v1"
    assert (
        writer.input_tokens,
        writer.output_tokens,
        writer.cache_read_tokens,
        writer.cache_write_tokens,
    ) == (120, 80, 30, 10)
    assert writer.cost_usd > 0
    assert writer.latency_ms >= 0
    assert writer.reserved_tokens > 0
    assert writer.trace_id == "run:1"
    assert (interviewer.run_id, interviewer.chapter) == (None, None)

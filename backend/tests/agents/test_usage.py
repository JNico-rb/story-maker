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
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import FakeAgent, Say, Script
from story_maker.agents.port import AgentPort, SessionRequest
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

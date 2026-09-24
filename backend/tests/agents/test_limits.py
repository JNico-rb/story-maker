"""Límites y desenlace de la sesión (003-C21..C24)."""

from __future__ import annotations

import asyncio
import dataclasses
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from claude_agent_sdk import ResultMessage
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import Call, FakeAgent, Hang, Say, Script
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.agents.sdk import final_from_result
from story_maker.agents.usage import Usage
from story_maker.config import Config
from story_maker.observability.null import NullObservability

FINAL_USAGE = Usage(
    input_tokens=1_200, output_tokens=800, cache_read_tokens=300, cache_write_tokens=100
)
CHAPTER = {"title": "Uno", "text": "limpio"}


def build_port(
    config: Config,
    fake: FakeAgent,
    policy: Any,
    ceiling: TokenCeiling,
    session_factory: sessionmaker[Session],
    workspace: Path,
) -> AgentPort:
    return AgentPort(
        agent=fake,
        config=config,
        ceiling=ceiling,
        policy=policy,
        telemetry=NullObservability(),
        session_factory=session_factory,
        workspace=workspace,
    )


async def test_exhausting_the_turns_keeps_the_usage(
    config: Config,
    port: AgentPort,
    fake: FakeAgent,
    make_request: Callable[..., SessionRequest],
) -> None:
    turns = config.roles["writer"].max_turns
    steps = tuple(Call("submit_chapter", {**CHAPTER, "text": f"v{i}"}) for i in range(turns + 2))
    fake.script("writer", "write", Script(steps=steps, usage=FINAL_USAGE, sdk_cost_usd=3.0))

    result = await port.run(make_request("writer", "write"))

    assert result.outcome == "turns_exhausted"
    assert result.usage == FINAL_USAGE
    assert result.cost_usd is not None
    assert result.cost_usd > 0
    assert [c.input["text"] for c in result.calls] == [f"v{i}" for i in range(turns)]


def result_message(**fields: Any) -> ResultMessage:
    base: dict[str, Any] = {
        "subtype": "success",
        "duration_ms": 1_000,
        "duration_api_ms": 900,
        "is_error": False,
        "num_turns": 2,
        "session_id": "sesion-de-prueba",
        "total_cost_usd": 0.9,
        "usage": {
            "input_tokens": 1_200,
            "output_tokens": 800,
            "cache_read_input_tokens": 300,
            "cache_creation_input_tokens": 100,
        },
        "result": "texto final",
    }
    base.update(fields)
    return ResultMessage(**base)


@pytest.mark.parametrize(
    ("fields", "ending"),
    [
        ({}, "completed"),
        ({"subtype": "error_max_turns", "is_error": True, "result": None}, "turns_exhausted"),
    ],
)
def test_the_sdk_final_result_keeps_its_usage_whatever_the_ending(
    fields: dict[str, Any], ending: str
) -> None:
    final = final_from_result(result_message(**fields))

    assert final.ending == ending
    assert final.usage == FINAL_USAGE
    assert final.sdk_cost_usd == 0.9


async def test_passing_the_session_timeout_interrupts_and_disconnects_keeping_a_final_usage(
    config: Config,
    fake: FakeAgent,
    policy: Any,
    ceiling: TokenCeiling,
    session_factory: sessionmaker[Session],
    workspace: Path,
    make_request: Callable[..., SessionRequest],
) -> None:
    port = build_port(
        dataclasses.replace(config, session_timeout_seconds=1),
        fake,
        policy,
        ceiling,
        session_factory,
        workspace,
    )
    fake.script("editor", None, Script(steps=(Hang(result=True),), usage=FINAL_USAGE))
    started = time.monotonic()

    result = await port.run(make_request("editor"))

    assert 1 <= time.monotonic() - started < 2
    assert result.outcome == "time_exhausted"
    assert result.usage == FINAL_USAGE
    assert fake.sessions[0].interrupted
    assert fake.sessions[0].disconnected


async def test_waiting_in_the_ceiling_counts_neither_in_the_session_time_nor_in_its_latency(
    config: Config,
    fake: FakeAgent,
    policy: Any,
    ceiling: TokenCeiling,
    session_factory: sessionmaker[Session],
    workspace: Path,
    run_id: int,
    make_request: Callable[..., SessionRequest],
) -> None:
    port = build_port(
        dataclasses.replace(config, session_timeout_seconds=1),
        fake,
        policy,
        ceiling,
        session_factory,
        workspace,
    )
    fake.script("judge", None, Script(steps=(Say("nota"),), usage=FINAL_USAGE))
    blocker = await ceiling.acquire(ceiling.limit, None)
    session = asyncio.create_task(port.run(make_request("judge", run_id=run_id)))

    await asyncio.sleep(1.5)
    ceiling.release(blocker)
    result = await session

    assert result.outcome == "completed"
    assert result.latency_ms < 1_000

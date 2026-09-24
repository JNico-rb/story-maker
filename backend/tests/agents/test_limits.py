"""Límites y desenlace de la sesión (003-C21..C24)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from claude_agent_sdk import ResultMessage

from story_maker.agents.fake import Call, FakeAgent, Script
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.agents.sdk import final_from_result
from story_maker.agents.usage import Usage
from story_maker.config import Config

FINAL_USAGE = Usage(
    input_tokens=1_200, output_tokens=800, cache_read_tokens=300, cache_write_tokens=100
)
CHAPTER = {"title": "Uno", "text": "limpio"}


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

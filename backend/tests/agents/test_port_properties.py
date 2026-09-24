"""Invariantes del puerto con secuencias generadas (003-I3)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic import BaseModel, model_validator
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import Call, FakeAgent, Script
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.agents.tools import ToolSpec
from story_maker.agents.usage import Usage
from story_maker.config import Config
from story_maker.observability.null import NullObservability
from story_maker.policy.types import DecisionDePolitica, PeticionDePolitica

USAGE = Usage(input_tokens=1, output_tokens=1, cache_read_tokens=0, cache_write_tokens=0)
PROPERTY = settings(
    max_examples=40, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)


def logged_tool(events: list[str]) -> ToolSpec:
    class Chapter(BaseModel):
        title: str
        text: str

        @model_validator(mode="before")
        @classmethod
        def log(cls, data: Any) -> Any:
            events.append(f"corre {data['n']}")
            return data

    return ToolSpec(name="submit_chapter", model=Chapter)


TOOLS = st.sampled_from(["submit_chapter", "Skill", "Bash"])
DECISIONS = st.sampled_from(["allow", "flag", "deny", "raise"])


@PROPERTY
@given(plan=st.lists(st.tuples(TOOLS, DECISIONS), max_size=6))
def test_no_tool_runs_without_an_allow_or_flag_decision_taken_before(
    plan: list[tuple[str, str]],
    config: Config,
    session_factory: sessionmaker[Session],
    workspace: Path,
    make_request: Callable[..., SessionRequest],
) -> None:
    events: list[str] = []
    decisions = iter(decision for _, decision in plan)

    class ScriptedPolicy:
        def decide(self, request: PeticionDePolitica) -> DecisionDePolitica:
            number = {c.path: c.texto for c in request.campos}["n"]
            decision = next(decisions)
            events.append(f"decide {number} {decision}")
            if decision == "raise":
                raise RuntimeError("motor caído")
            return DecisionDePolitica(decision=decision, rule="motivo")  # type: ignore[arg-type]

    fake = FakeAgent()
    steps = tuple(
        Call(tool, {"n": str(i), "title": "t", "text": "x"}) for i, (tool, _) in enumerate(plan)
    )
    fake.script("writer", "write", Script(steps=steps, usage=USAGE))
    port = AgentPort(
        agent=fake,
        config=config,
        ceiling=TokenCeiling(config.token_ceiling),
        policy=ScriptedPolicy(),
        telemetry=NullObservability(),
        session_factory=session_factory,
        workspace=workspace,
    )

    result = asyncio.run(port.run(make_request("writer", "write", tools=(logged_tool(events),))))

    ran = {call.input["n"] for call in result.calls if call.status == "accepted"}
    for index, event in enumerate(events):
        if event.startswith("corre "):
            number = event.split()[1]
            assert events[index - 1] in (f"decide {number} allow", f"decide {number} flag")
    for i, (_tool, decision) in enumerate(plan):
        if decision in ("deny", "raise"):
            assert f"corre {i}" not in events
            assert str(i) not in ran
    if "raise" in [d for _, d in plan]:
        stop = [d for _, d in plan].index("raise")
        assert len([e for e in events if e.startswith("decide")]) == stop + 1

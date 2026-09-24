"""`TechoDeTokens`: reserva, espera en orden, espera acotada, reserva imposible (003-C16..C20)."""

from __future__ import annotations

import dataclasses
from collections.abc import Callable
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import FakeAgent, Say, Script
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.agents.tools import ToolSpec
from story_maker.agents.usage import Usage
from story_maker.config import Config
from story_maker.observability.null import NullObservability
from story_maker.store.models import RoleSession

USAGE = Usage(input_tokens=1, output_tokens=1, cache_read_tokens=0, cache_write_tokens=0)
SKILL_FILE = Path(".claude") / "skills" / "personalizacion-natural" / "SKILL.md"


def with_role(config: Config, role: str, **limits: Any) -> Config:
    roles = dict(config.roles)
    roles[role] = dataclasses.replace(config.roles[role], **limits)
    return dataclasses.replace(config, roles=roles)


def build_port(
    config: Config,
    fake: FakeAgent,
    policy: Any,
    session_factory: sessionmaker[Session],
    workspace: Path,
    ceiling: TokenCeiling | None = None,
) -> AgentPort:
    return AgentPort(
        agent=fake,
        config=config,
        ceiling=ceiling or TokenCeiling(config.token_ceiling),
        policy=policy,
        telemetry=NullObservability(),
        session_factory=session_factory,
        workspace=workspace,
    )


def sent_chars(request: SessionRequest, workspace: Path) -> int:
    claude_md = (workspace / "CLAUDE.md").read_text(encoding="utf-8")
    schemas = sum(len(spec.schema_text()) for spec in request.tools)
    return len(request.prompt) + len(claude_md) + schemas + len(request.message)


async def test_the_reservation_is_the_estimated_input_plus_the_growth_of_the_turns(
    config: Config,
    fake: FakeAgent,
    policy: Any,
    session_factory: sessionmaker[Session],
    workspace: Path,
    make_request: Callable[..., SessionRequest],
    tool_named: Callable[..., ToolSpec],
) -> None:
    interviewer = with_role(config, "interviewer", max_turns=4, max_output_tokens=2000)
    base = make_request("interviewer", message="")
    request = dataclasses.replace(base, message="m" * (12_001 - sent_chars(base, workspace)))
    assert sent_chars(request, workspace) == 12_001
    fake.script("interviewer", None, Script(steps=(Say("hola"),), usage=USAGE))
    port = build_port(interviewer, fake, policy, session_factory, workspace)

    assert port.reservation(request) == 3_001 + 3 * 2_000
    single_turn = with_role(interviewer, "interviewer", max_turns=1)
    assert (
        build_port(single_turn, fake, policy, session_factory, workspace).reservation(request)
        == 3_001
    )

    result = await port.run(request)

    assert result.reserved_tokens == 9_001
    with session_factory() as session:
        row = session.get(RoleSession, result.role_session_id)
        assert row is not None
        assert row.reserved_tokens == 9_001


def test_in_the_writer_the_skill_characters_count_in_the_input(
    config: Config,
    fake: FakeAgent,
    policy: Any,
    session_factory: sessionmaker[Session],
    workspace: Path,
    make_request: Callable[..., SessionRequest],
) -> None:
    skill = workspace / SKILL_FILE
    skill.parent.mkdir(parents=True)
    skill.write_text("s" * 4_000, encoding="utf-8")
    writer = with_role(config, "writer", max_turns=1)
    request = make_request("writer", "write")
    port = build_port(writer, fake, policy, session_factory, workspace)

    assert port.reservation(request) == -(-(sent_chars(request, workspace) + 4_000) // 4)

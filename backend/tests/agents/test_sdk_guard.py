"""En la suite, el adaptador del SDK no abre sesiones ni lanza el CLI (003-I6)."""

from __future__ import annotations

import asyncio
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import anyio
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.agents.sdk import RealModelInTests, SdkAgent
from story_maker.config import Config
from story_maker.observability.null import NullObservability
from story_maker.settings import Settings
from story_maker.store.models import RoleSession


async def test_the_sdk_adapter_cannot_open_a_session_in_the_suite_and_launches_nothing(
    config: Config,
    ceiling: TokenCeiling,
    policy: Any,
    telemetry: NullObservability,
    session_factory: sessionmaker[Session],
    workspace: Path,
    make_request: Callable[..., SessionRequest],
    make_settings: Callable[..., Settings],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launched: list[Any] = []

    def record(*args: Any, **kwargs: Any) -> Any:
        launched.append(args)
        raise AssertionError("se intentó lanzar un subproceso")

    monkeypatch.setattr(anyio, "open_process", record)
    monkeypatch.setattr(subprocess, "Popen", record)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", record)
    port = AgentPort(
        agent=SdkAgent(make_settings(), workspace=workspace),
        config=config,
        ceiling=ceiling,
        policy=policy,
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace,
    )

    with pytest.raises(RealModelInTests):
        await port.run(make_request("interviewer"))

    assert launched == []
    assert ceiling.in_use == 0
    with session_factory() as session:
        assert session.scalars(select(RoleSession)).all() == []

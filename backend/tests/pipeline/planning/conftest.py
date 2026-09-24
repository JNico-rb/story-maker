"""Fixtures de la sesión del planner: config, base, doble falso y puerto con la policy real de
producción (`pipeline/planning/session.py`), no el doble de `tests/agents/`."""

from __future__ import annotations

import dataclasses
import datetime as dt
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import FakeAgent
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.config import Config, load_config
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Trace
from story_maker.pipeline.planning.session import BannedTermsPolicy, submit_plan_tool
from story_maker.settings import ROOT
from story_maker.store.models import BannedTerm, Novel, Run, User, Version
from story_maker.store.session import create_schema, make_engine, make_session_factory


@pytest.fixture
def config() -> Config:
    base = load_config(ROOT / "config.json")
    return dataclasses.replace(base, max_retries={**base.max_retries, "plan": 2})


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    eng = make_engine(tmp_path / "story-maker.db")
    create_schema(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Session]:
    return make_session_factory(engine)


@pytest.fixture
def novel_id(session_factory: sessionmaker[Session]) -> int:
    now = dt.datetime(2026, 9, 24, 12, 0)
    with session_factory() as session:
        user = User(email="cliente@example.com", password_hash="x", created_at=now)
        session.add(user)
        session.flush()
        novel = Novel(user_id=user.id, title=None, embedding_model="e5", created_at=now)
        session.add(novel)
        session.commit()
        return novel.id


@pytest.fixture
def user_id(session_factory: sessionmaker[Session], novel_id: int) -> int:
    with session_factory() as session:
        novel = session.get(Novel, novel_id)
        assert novel is not None
        return novel.user_id


@pytest.fixture
def run_id(session_factory: sessionmaker[Session], novel_id: int) -> int:
    with session_factory() as session:
        run = Run(
            novel_id=novel_id,
            type="generation",
            status="running",
            phase="planning",
            resumes=0,
            created_at=dt.datetime(2026, 9, 24, 12, 0),
        )
        session.add(run)
        session.commit()
        return run.id


@pytest.fixture
def candidate_version_id(session_factory: sessionmaker[Session], novel_id: int) -> int:
    """Una fila de `versions` desnuda, solo para satisfacer la clave ajena de
    `validator_results.version_id` en las pruebas: no es el canon del brief de 009-C10 (010-C01,
    todavía bloqueado)."""
    with session_factory() as session:
        version = Version(
            novel_id=novel_id,
            status="candidate",
            number=None,
            base_version_id=None,
            changed_chapters=[],
            created_at=dt.datetime(2026, 9, 24, 12, 0),
        )
        session.add(version)
        session.commit()
        return version.id


def ban(
    session_factory: sessionmaker[Session],
    *,
    level: str,
    term: str,
    type_: str = "word",
    keywords: list[str] | None = None,
    user_id: int | None = None,
    novel_id: int | None = None,
) -> None:
    with session_factory() as session:
        session.add(
            BannedTerm(
                level=level,
                user_id=user_id,
                novel_id=novel_id,
                term=term,
                type=type_,
                keywords=keywords,
                normalized=term.lower(),
            )
        )
        session.commit()


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    path = tmp_path / "harness_workspace"
    path.mkdir()
    (path / "CLAUDE.md").write_text("Escribe en español.", encoding="utf-8")
    return path


@pytest.fixture
def telemetry() -> NullObservability:
    return NullObservability()


@pytest.fixture
def fake() -> FakeAgent:
    return FakeAgent()


@pytest.fixture
def ceiling(config: Config) -> TokenCeiling:
    return TokenCeiling(config.token_ceiling)


@pytest.fixture
def port(
    fake: FakeAgent,
    config: Config,
    ceiling: TokenCeiling,
    session_factory: sessionmaker[Session],
    telemetry: NullObservability,
    workspace: Path,
) -> AgentPort:
    return AgentPort(
        agent=fake,
        config=config,
        ceiling=ceiling,
        policy=BannedTermsPolicy(session_factory),
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace,
    )


@pytest.fixture
def plan_request(user_id: int, novel_id: int, run_id: int) -> SessionRequest:
    return SessionRequest(
        role="planner",
        mode="plan",
        user_id=user_id,
        novel_id=novel_id,
        run_id=run_id,
        prompt="Prompt del planner",
        prompt_version="v1",
        message="Ventana del planner",
        tools=(submit_plan_tool(),),
        trace=Trace(key=f"run:{run_id}"),
    )


def audit_rows(session_factory: sessionmaker[Session]) -> list[dict[str, Any]]:
    from sqlalchemy import select

    from story_maker.store.models import AuditLog

    with session_factory() as session:
        return [
            {"decision": r.decision, "rule": r.rule, "tool": r.tool, "origin": r.origin}
            for r in session.scalars(select(AuditLog).order_by(AuditLog.id)).all()
        ]

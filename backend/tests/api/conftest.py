"""Fixtures de la API de 008: app con `AgentPort` real (doble falso del agente + motor de
políticas real, `RealPolicyEngine`), cliente HTTP autenticado y ayudas de fecha fija."""

from __future__ import annotations

import dataclasses
import datetime as dt
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import FakeAgent
from story_maker.agents.port import AgentPort
from story_maker.api.app import create_app
from story_maker.config import Config, load_config
from story_maker.observability.null import NullObservability
from story_maker.policy.real_engine import RealPolicyEngine
from story_maker.settings import ROOT
from story_maker.store.session import create_schema, make_engine, make_session_factory

JWT_SECRET = "x" * 32
NOW = dt.datetime(2026, 9, 24, 12, 0, 0)
EMAIL = "cliente@example.com"
PASSWORD = "contraseña-larga"


@pytest.fixture
def config() -> Config:
    """La del repositorio, con el modelo de incrustación M1, techo amplio y más turnos para el
    entrevistador y el extractor: caben los guiones largos de las pruebas de esta spec."""
    base = load_config(ROOT / "config.json")
    roles = dict(base.roles)
    for role in ("interviewer", "extractor"):
        roles[role] = dataclasses.replace(roles[role], max_turns=12)
    return dataclasses.replace(base, embedding_model="M1", token_ceiling=50_000, roles=roles)


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
def workspace(tmp_path: Path) -> Path:
    path = tmp_path / "harness_workspace"
    (path / "prompts").mkdir(parents=True)
    (path / "CLAUDE.md").write_text("Escribe en español.", encoding="utf-8")
    (path / "prompts" / "interviewer.md").write_text("Eres el entrevistador.", encoding="utf-8")
    (path / "prompts" / "extractor.md").write_text("Eres el extractor.", encoding="utf-8")
    return path


@pytest.fixture
def fake() -> FakeAgent:
    return FakeAgent()


@pytest.fixture
def telemetry() -> NullObservability:
    return NullObservability()


@pytest.fixture
def ceiling(config: Config) -> TokenCeiling:
    return TokenCeiling(config.token_ceiling)


@pytest.fixture
def agent_port(
    fake: FakeAgent,
    config: Config,
    ceiling: TokenCeiling,
    session_factory: sessionmaker[Session],
    workspace: Path,
    telemetry: NullObservability,
) -> AgentPort:
    return AgentPort(
        agent=fake,
        config=config,
        ceiling=ceiling,
        policy=RealPolicyEngine(session_factory, base_url="http://127.0.0.1:8000"),
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace,
    )


@pytest.fixture
def clock() -> Callable[[], dt.datetime]:
    return lambda: NOW


@pytest.fixture
def client(
    session_factory: sessionmaker[Session],
    agent_port: AgentPort,
    telemetry: NullObservability,
    config: Config,
    workspace: Path,
    clock: Callable[[], dt.datetime],
) -> TestClient:
    app = create_app(
        session_factory=session_factory,
        jwt_secret=JWT_SECRET,
        clock=clock,
        agent_port=agent_port,
        telemetry=telemetry,
        config=config,
        workspace=workspace,
    )
    return TestClient(app)


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    client.post("/api/auth/register", json={"email": EMAIL, "password": PASSWORD})
    response = client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_client_headers(client: TestClient) -> dict[str, str]:
    client.post("/api/auth/register", json={"email": "otro@example.com", "password": PASSWORD})
    response = client.post(
        "/api/auth/login", json={"email": "otro@example.com", "password": PASSWORD}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

"""Fixtures del puerto de agente: config, base, política doble, workspace y puerto con el doble."""

from __future__ import annotations

import dataclasses
import datetime as dt
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import FakeAgent
from story_maker.agents.policy_port import PolicyDecision, PolicyRequest
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.agents.tools import ToolSpec
from story_maker.config import Config, load_config
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Trace
from story_maker.settings import ROOT, Settings
from story_maker.store.models import Novel, Run, User
from story_maker.store.session import create_schema, make_engine, make_session_factory


class ChapterInput(BaseModel):
    title: str
    text: str


class BriefInput(BaseModel):
    field: str
    value: str


def own_tool(name: str, model: type[BaseModel] = BriefInput) -> ToolSpec:
    return ToolSpec(name=name, model=model, description=f"Tool de prueba {name}")


CHAPTER_TOOL = ToolSpec(
    name="submit_chapter",
    model=ChapterInput,
    description="Entrega el capítulo",
    narrative=("title", "text"),
)


class DoublePolicy:
    """Doble del `MotorDePoliticas`: registra cada petición y decide con `rule`."""

    def __init__(self, rule: Callable[[PolicyRequest], PolicyDecision] | None = None) -> None:
        self.requests: list[PolicyRequest] = []
        self.rule = rule or (lambda _request: PolicyDecision(decision="allow"))

    def decide(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return self.rule(request)


@pytest.fixture
def config() -> Config:
    """La del repositorio con techo de prueba y writer de 8 turnos: caben los guiones largos."""
    base = load_config(ROOT / "config.json")
    roles = dict(base.roles)
    roles["writer"] = dataclasses.replace(roles["writer"], max_turns=8)
    return dataclasses.replace(base, token_ceiling=50_000, roles=roles)


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
def run_id(session_factory: sessionmaker[Session], novel_id: int) -> int:
    with session_factory() as session:
        run = Run(
            novel_id=novel_id,
            type="generation",
            status="running",
            resumes=0,
            created_at=dt.datetime(2026, 9, 24, 12, 0),
        )
        session.add(run)
        session.commit()
        return run.id


@pytest.fixture
def user_id(session_factory: sessionmaker[Session], novel_id: int) -> int:
    with session_factory() as session:
        novel = session.get(Novel, novel_id)
        assert novel is not None
        return novel.user_id


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    path = tmp_path / "harness_workspace"
    path.mkdir()
    (path / "CLAUDE.md").write_text("Escribe en español.", encoding="utf-8")
    return path


@pytest.fixture
def policy() -> DoublePolicy:
    return DoublePolicy()


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
    policy: DoublePolicy,
    telemetry: NullObservability,
    session_factory: sessionmaker[Session],
    workspace: Path,
) -> AgentPort:
    return AgentPort(
        agent=fake,
        config=config,
        ceiling=ceiling,
        policy=policy,
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace,
    )


@pytest.fixture
def make_request(user_id: int, novel_id: int) -> Callable[..., SessionRequest]:
    def make(role: str, mode: str | None = None, **overrides: Any) -> SessionRequest:
        fields: dict[str, Any] = {
            "role": role,
            "mode": mode,
            "user_id": user_id,
            "novel_id": novel_id,
            "prompt": f"Prompt de {role}",
            "prompt_version": "v1",
            "message": "Mensaje de la llamada",
            "tools": default_tools(role, mode),
            "trace": Trace(key="run:1"),
        }
        fields.update(overrides)
        return SessionRequest(**fields)

    return make


def default_tools(role: str, mode: str | None) -> tuple[ToolSpec, ...]:
    names = {
        ("interviewer", None): "update_brief",
        ("extractor", None): "submit_facts",
        ("planner", "plan"): "submit_plan",
        ("planner", "change"): "propose_change",
        ("editor", None): "submit_review",
        ("judge", None): "submit_evaluation",
        ("visual_reviewer", None): "submit_visual_review",
    }
    if role == "writer":
        return (CHAPTER_TOOL,)
    return (own_tool(names[(role, mode)]),)


@pytest.fixture
def chapter_tool() -> ToolSpec:
    return CHAPTER_TOOL


@pytest.fixture
def tool_named() -> Callable[..., ToolSpec]:
    return own_tool


@pytest.fixture
def make_settings(tmp_path: Path) -> Callable[..., Settings]:
    """Ajustes de prueba, sin `.env`; las claves, marcadores de prueba."""

    def make(**overrides: Any) -> Settings:
        fields: dict[str, Any] = {
            "data_dir": tmp_path / "data",
            "config_path": ROOT / "config.json",
            "base_url": "http://127.0.0.1:8000",
            "frontend_dist": tmp_path / "dist",
            "jwt_secret": "secreto-de-prueba-de-32-caracteres!",
            "llm_provider": "claude_login",
            "formal_verifier": "github",
            "github_repository": None,
            "lean_workflow": None,
            "github_token": None,
            "claude_code_oauth_token": None,
            "anthropic_base_url": None,
            "anthropic_auth_token": None,
            "openrouter_api_key": None,
            "langfuse_public_key": None,
            "langfuse_secret_key": None,
            "langfuse_base_url": None,
            "langfuse_prompt_label": None,
        }
        fields.update(overrides)
        return Settings(**fields)

    return make

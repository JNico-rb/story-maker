"""El montaje único de la aplicación que comparten `serve`, `example` y `evals run`
(`architecture.md` §1.4: un proceso; spec 031)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI

from story_maker import settings as settings_module
from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.port import Agent, AgentPort
from story_maker.agents.sdk import SdkAgent
from story_maker.api.app import create_app
from story_maker.api.auth import Clock, utc_now
from story_maker.config import Config
from story_maker.observability.port import ObservabilityPort
from story_maker.policy.real_engine import RealPolicyEngine
from story_maker.settings import Settings
from story_maker.store.session import make_engine, make_session_factory

DB_FILENAME = "story-maker.db"


@dataclass(frozen=True)
class Adapters:
    """Lo que sale del proceso; las pruebas lo sustituyen por sus dobles."""

    agent: Agent


def workspace() -> Path:
    return settings_module.ROOT / "backend" / "harness_workspace"


def real_adapters(settings: Settings, config: Config) -> Adapters:
    """El agente de `LLM_PROVIDER` (§15.2)."""
    return Adapters(agent=SdkAgent(settings, workspace=workspace()))


def build_app(
    settings: Settings,
    config: Config,
    telemetry: ObservabilityPort,
    adapters: Adapters,
    *,
    clock: Clock = utc_now,
) -> FastAPI:
    """La API entera sobre la base de `STORY_MAKER_DATA_DIR`, con la SPA si está compilada."""
    session_factory = make_session_factory(make_engine(settings.data_dir / DB_FILENAME))
    policy = RealPolicyEngine(session_factory, base_url=settings.base_url)
    agent_port = AgentPort(
        agent=adapters.agent,
        config=config,
        ceiling=TokenCeiling(config.token_ceiling),
        policy=policy,
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace(),
    )
    return create_app(
        settings.frontend_dist,
        session_factory=session_factory,
        jwt_secret=settings.jwt_secret,
        access_token_hours=config.access_token_hours,
        clock=clock,
        agent_port=agent_port,
        telemetry=telemetry,
        config=config,
        workspace=workspace(),
        policy=policy,
    )

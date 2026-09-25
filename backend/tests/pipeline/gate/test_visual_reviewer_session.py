"""017-C03 · La sesión del revisor solo navega la vista (y 017-I6)."""

from __future__ import annotations

import asyncio
import dataclasses
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed
from tests.pipeline.gate.visual import (
    BASE_URL,
    faithful,
    job_of,
    make_settings,
    make_stage,
    reviewer_script,
    reviewer_sessions,
    seed_visual,
)

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import Call, FakeAgent
from story_maker.agents.port import AgentPort
from story_maker.agents.sdk import SdkAgent
from story_maker.config import Config
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Span, Trace
from story_maker.pipeline.production import Production
from story_maker.policy.real_engine import RealPolicyEngine
from story_maker.store.models import AuditLog

BROWSER_TOOLS = {"browser_navigate", "browser_snapshot", "browser_click"}
OWN = "submit_visual_review"


class NoHooks:
    """Los hooks no corren al construir la configuración del SDK."""

    def before_tool(self, call_id: str, tool: str, tool_input: dict[str, Any]) -> str | None:
        raise AssertionError

    def run_tool(self, tool: str, tool_input: dict[str, Any]) -> tuple[str, bool]:
        raise AssertionError

    def after_tool(self, call_id: str, tool: str) -> str | None:
        raise AssertionError

    @property
    def stopping(self) -> bool:
        return False


def test_the_reviewer_session_uses_its_model_its_four_tools_and_only_the_browser_mcp(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    config: Config,
    trace: Trace,
    workspace: Path,
    tmp_path: Path,
) -> None:
    seed_visual(session_factory, at_gate)
    settings = make_settings(tmp_path / "data")
    fake.script("visual_reviewer", None, reviewer_script(faithful()))

    asyncio.run(make_stage(production, settings)(job_of(at_gate), trace))

    [session] = reviewer_sessions(fake)
    assert session.profile.model == config.roles["visual_reviewer"].model
    assert set(session.profile.whitelist) == {*BROWSER_TOOLS, OWN}
    options = SdkAgent(settings, workspace=workspace).session_options(
        session.request, session.profile, NoHooks()
    )
    assert options.tools == []
    assert {name.rsplit("__", 1)[-1] for name in options.allowed_tools} == {*BROWSER_TOOLS, OWN}
    assert isinstance(options.mcp_servers, dict)
    external = [s for s in options.mcp_servers.values() if s.get("type") != "sdk"]
    [browser] = external
    args = browser["args"]
    assert "@playwright/mcp@0.0.82" in args
    assert args[args.index("--browser") + 1] == "msedge"
    assert Path(args[args.index("--output-dir") + 1]).is_relative_to(settings.data_dir)


@pytest.fixture
def config(config: Config) -> Config:
    """Turnos de sobra para recorrer la tabla de 017-C03 y entregar."""
    reviewer = dataclasses.replace(config.roles["visual_reviewer"], max_turns=20)
    return dataclasses.replace(config, roles={**config.roles, "visual_reviewer": reviewer})


@pytest.fixture
def navigating_port(
    fake: FakeAgent,
    config: Config,
    telemetry: NullObservability,
    session_factory: sessionmaker[Session],
    workspace: Path,
) -> AgentPort:
    """El puerto con el motor real de 005 y el origen de `STORY_MAKER_BASE_URL`."""
    return AgentPort(
        agent=fake,
        config=config,
        ceiling=TokenCeiling(config.token_ceiling),
        policy=RealPolicyEngine(session_factory, base_url=BASE_URL),
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace,
    )


def _spans(spans: list[Span]) -> list[Span]:
    return [s for span in spans for s in (span, *_spans(span.children))]


DENIED = [
    Call("browser_navigate", {"url": "http://127.0.0.1:9000/view/versions/1"}),
    Call("browser_navigate", {"url": "http://example.com:8000/view/versions/1"}),
    Call("browser_navigate", {"url": "http://localhost:8000/view/versions/1"}),
    Call("browser_navigate", {"url": "https://127.0.0.1:8000/view/versions/1"}),
    Call("browser_navigate", {"url": "file:///C:/novela.html"}),
    Call("browser_type", {"text": "hola"}),
    Call("Bash", {"command": "dir"}),
    Call("Skill", {"skill": "personalizacion-natural"}),
]


def test_the_policy_hook_lets_the_reviewer_navigate_only_the_view_origin_and_it_still_delivers(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    navigating_port: AgentPort,
    trace: Trace,
    tmp_path: Path,
) -> None:
    seed_visual(session_factory, at_gate)
    settings = make_settings(tmp_path / "data")
    stage = make_stage(dataclasses.replace(production, port=navigating_port), settings)
    allowed = [
        Call("browser_navigate", {"url": stage.view_url(at_gate.version_id)}),
        Call("browser_navigate", {"url": f"{BASE_URL}/view/versions/999?token=x"}),
    ]
    fake.script("visual_reviewer", None, reviewer_script(faithful(), steps=(*allowed, *DENIED)))

    asyncio.run(stage(job_of(at_gate), trace))

    [session] = reviewer_sessions(fake)
    with session_factory() as db:
        rows = db.query(AuditLog).filter(AuditLog.role == "visual_reviewer").order_by(AuditLog.id)
        decisions = [(r.tool, r.decision, r.origin) for r in rows]
    assert decisions[:2] == [("browser_navigate", "allow", "policy_hook")] * 2
    assert decisions[2:10] == [(c.tool, "deny", "policy_hook") for c in DENIED]
    assert decisions[10] == (OWN, "allow", "policy_hook")
    reads = session.reads
    assert reads[:2] == ["Hecho.", "Hecho."]
    assert all(read.startswith(("lista-blanca", "origen-de-navegacion")) for read in reads[2:10])
    assert len(session.request.tools) == 1
    warnings = [s for s in _spans(trace.spans) if s.level == "WARNING"]
    assert [s.name for s in warnings] == [f"tool:{c.tool}" for c in DENIED]
    assert all(s.status_message for s in warnings)
    assert len([c for c in session.hooks.calls if c.own and c.status == "accepted"]) == 1

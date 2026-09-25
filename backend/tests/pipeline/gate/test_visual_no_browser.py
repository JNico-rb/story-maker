"""017-C15 · Sin navegador, la ejecución se interrumpe y no publica."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import USAGE, Seed
from tests.pipeline.gate.conftest import (
    GateKit,
    evaluation,
    gate_passes,
    run_of,
    script_judges,
)
from tests.pipeline.gate.visual import make_settings, make_stage, seed_visual, with_stage

from story_maker.agents.fake import Fail, FakeAgent, Script
from story_maker.observability.port import Trace
from story_maker.pipeline.production import Production
from story_maker.pipeline.runs import RunStop
from story_maker.store.models import RoleSession, Version


def test_without_a_browser_the_run_is_interrupted_with_provider_error_and_nothing_publishes(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    kit: GateKit,
    trace: Trace,
    tmp_path: Path,
) -> None:
    seed_visual(session_factory, at_gate)
    script_judges(fake, evaluation(4))
    # El servidor Playwright MCP no conecta: el transporte de la sesión cae.
    fake.script("visual_reviewer", None, Script(steps=(Fail(),), usage=USAGE))
    gate = with_stage(kit, make_stage(production, make_settings(tmp_path)))

    with pytest.raises(RunStop) as stop:
        asyncio.run(gate(at_gate.run_id, trace))

    assert (stop.value.status, stop.value.reason) == ("interrupted", "provider_error")
    assert "navegador" in stop.value.detail
    with session_factory() as session:
        [row] = session.query(RoleSession).filter(RoleSession.role == "visual_reviewer").all()
        assert row.outcome == "infrastructure_failure"
        assert session.get_one(Version, at_gate.version_id).status == "candidate"
    assert kit.pdf.calls == []
    assert gate_passes(session_factory, at_gate.run_id) == []
    assert run_of(session_factory, at_gate.run_id).status != "published"

"""Cada sesión reserva en el techo, y una que no cabe nunca hace fallar (011-C09)."""

from __future__ import annotations

import asyncio
import dataclasses
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    NOW,
    BannedPolicy,
    FixedWindows,
    PhaseDouble,
    Seed,
    chapter_call,
    editor_script,
    review,
    script_accepted_chapters,
    writer_script,
)

from story_maker.agents.ceiling import TokenCeiling, estimate_tokens
from story_maker.agents.fake import FakeAgent, FakeSession
from story_maker.agents.port import AgentPort
from story_maker.agents.profiles import role_profile
from story_maker.config import Config
from story_maker.observability.null import NullObservability
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import Production
from story_maker.store.models import Checkpoint, RoleSession, Run


def expected_reservation(config: Config, workspace: Path, session: FakeSession) -> int:
    """Los textos fijos (prompt, `CLAUDE.md`, schemas) más la ventana, con el estimador de 003,
    más (`max_turns` - 1) · `max_output_tokens` del rol."""
    request = session.request
    profile = role_profile(config, request.role, request.mode)
    chars = (
        len(request.prompt)
        + len((workspace / "CLAUDE.md").read_text(encoding="utf-8"))
        + sum(len(t.schema_text()) for t in request.tools)
        + len(request.message)
    )
    return estimate_tokens(chars) + (profile.max_turns - 1) * profile.max_output_tokens


def set_last_chapter(session_factory: sessionmaker[Session], run_id: int) -> None:
    """Capítulos 1 a 9 con su punto de control: solo queda el 10."""
    with session_factory() as session:
        session.get_one(Run, run_id).chapter = 10
        session.add_all(Checkpoint(run_id=run_id, chapter=k, created_at=NOW) for k in range(1, 10))
        session.commit()


async def test_each_writer_and_editor_session_reserves_its_window_plus_the_turn_growth(
    orchestrator: Orchestrator,
    fake: FakeAgent,
    config: Config,
    workspace: Path,
    seed: Seed,
    session_factory: sessionmaker[Session],
) -> None:
    script_accepted_chapters(fake, 10)

    await orchestrator.execute(seed.run_id)

    with session_factory() as session:
        reserved = [
            s.reserved_tokens
            for s in session.query(RoleSession)
            .filter_by(run_id=seed.run_id)
            .order_by(RoleSession.id)
        ]
    assert [s.request.role for s in fake.sessions[:2]] == ["writer", "editor"]
    assert reserved == [expected_reservation(config, workspace, s) for s in fake.sessions]


async def test_a_session_that_does_not_fit_waits_and_opens_when_there_is_room(
    orchestrator: Orchestrator,
    fake: FakeAgent,
    ceiling: TokenCeiling,
    seed: Seed,
    session_factory: sessionmaker[Session],
) -> None:
    set_last_chapter(session_factory, seed.run_id)
    fake.script("writer", "write", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(review()))
    other = await ceiling.acquire(ceiling.limit - 10, timeout=None)

    task = asyncio.create_task(orchestrator.execute(seed.run_id))
    for _ in range(20):
        await asyncio.sleep(0)

    assert fake.sessions == []
    assert not task.done()
    ceiling.release(other)
    await task
    assert [s.request.role for s in fake.sessions] == ["writer", "editor"]
    with session_factory() as session:
        assert session.get_one(Run, seed.run_id).status == "running"


async def test_a_session_that_would_never_fit_opens_nothing_and_fails_with_infeasible_config(
    production: Production,
    planning: PhaseDouble,
    gate: PhaseDouble,
    fake: FakeAgent,
    config: Config,
    policy: BannedPolicy,
    telemetry: NullObservability,
    workspace: Path,
    seed: Seed,
    session_factory: sessionmaker[Session],
) -> None:
    small = dataclasses.replace(config, token_ceiling=5000)
    port = AgentPort(
        agent=fake,
        config=small,
        ceiling=TokenCeiling(small.token_ceiling),
        policy=policy,
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace,
    )
    big = FixedWindows(residents={"style_sheet": "x" * 40_000})
    production = dataclasses.replace(production, port=port, config=small, windows=big)
    orchestrator = Orchestrator(production=production, planning=planning, gate=gate)
    fake.script("writer", "write", writer_script(chapter_call()))

    await orchestrator.execute(seed.run_id)

    assert fake.sessions == []
    with session_factory() as session:
        run = session.get_one(Run, seed.run_id)
        assert (run.status, run.reason) == ("failed", "infeasible_config")
        assert session.query(RoleSession).count() == 0
    assert gate.calls == []

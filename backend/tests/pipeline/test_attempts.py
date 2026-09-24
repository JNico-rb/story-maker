"""Intentos de un capítulo: sesiones sin entrega, revisión del editor, veredicto por código,
reescritura y agotamiento (011-C14 a 011-C18)."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    BannedPolicy,
    Seed,
    chapter_call,
    editor_script,
    review,
    writer_script,
)

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import Call, FakeAgent, Hang
from story_maker.agents.port import AgentPort
from story_maker.config import Config
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Trace
from story_maker.pipeline.production import ChapterProducer, Production
from story_maker.store.models import Attempt, RoleSession

SKILL = Call("Skill", {"skill": "personalizacion-natural"})


def attempts(session_factory: sessionmaker[Session], run_id: int, chapter: int) -> list[Any]:
    with session_factory() as session:
        rows = session.query(Attempt).filter_by(run_id=run_id, chapter=chapter)
        return [(a.number, a.outcome) for a in rows.order_by(Attempt.id)]


def message(fake: FakeAgent, index: int) -> dict[str, Any]:
    parsed: dict[str, Any] = json.loads(fake.sessions[index].request.message)
    return parsed


def roles(fake: FakeAgent) -> list[tuple[str, str | None]]:
    return [(s.request.role, s.request.mode) for s in fake.sessions]


async def test_a_writer_session_out_of_turns_is_a_failed_attempt_plus_its_rejections(
    producer: ChapterProducer,
    fake: FakeAgent,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    fake.script("writer", "write", writer_script(chapter_call(1501), *[SKILL] * 8))
    fake.script("writer", "rewrite", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(review()))

    await producer.produce_chapter(seed.run_id, 4, trace)

    with session_factory() as session:
        first = session.query(RoleSession).filter_by(role="writer").order_by(RoleSession.id).first()
        assert first is not None
        assert first.outcome == "turns_exhausted"
    assert attempts(session_factory, seed.run_id, 4) == [
        (1, "rewrite"),
        (2, "rewrite"),
        (3, "accept"),
    ]
    assert roles(fake) == [("writer", "write"), ("writer", "rewrite"), ("editor", None)]
    rewrite = message(fake, 1)
    assert rewrite["window"] == message(fake, 0)["window"]
    assert [d["validator"] for d in rewrite["call_inputs"]["defects"]] == ["longitud-capitulo"]


async def test_a_writer_session_that_ends_without_delivering_is_a_failed_attempt(
    producer: ChapterProducer,
    fake: FakeAgent,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    fake.script("writer", "write", writer_script())
    fake.script("writer", "rewrite", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(review()))

    await producer.produce_chapter(seed.run_id, 4, trace)

    assert attempts(session_factory, seed.run_id, 4) == [(1, "rewrite"), (2, "accept")]
    assert roles(fake) == [("writer", "write"), ("writer", "rewrite"), ("editor", None)]
    rewrite = message(fake, 1)
    assert rewrite["window"] == message(fake, 0)["window"]
    assert "defects" not in rewrite["call_inputs"]


async def test_a_writer_session_out_of_time_is_a_failed_attempt(
    production: Production,
    fake: FakeAgent,
    config: Config,
    policy: BannedPolicy,
    telemetry: NullObservability,
    workspace: Path,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    quick = dataclasses.replace(config, session_timeout_seconds=1)
    port = AgentPort(
        agent=fake,
        config=quick,
        ceiling=TokenCeiling(quick.token_ceiling),
        policy=policy,
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace,
    )
    producer = ChapterProducer(dataclasses.replace(production, port=port, config=quick))
    fake.script("writer", "write", writer_script(Hang(), end=False))
    fake.script("writer", "rewrite", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(review()))

    await producer.produce_chapter(seed.run_id, 4, trace)

    with session_factory() as session:
        outcomes = [r.outcome for r in session.query(RoleSession).order_by(RoleSession.id)]
    assert outcomes == ["time_exhausted", "completed", "completed"]
    assert attempts(session_factory, seed.run_id, 4) == [(1, "rewrite"), (2, "accept")]
    assert roles(fake) == [("writer", "write"), ("writer", "rewrite"), ("editor", None)]

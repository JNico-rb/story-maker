"""Intentos de un capítulo: sesiones sin entrega, revisión del editor, veredicto por código,
reescritura y agotamiento (011-C14 a 011-C18)."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    BANNED,
    CRITERIA,
    NOW,
    BannedPolicy,
    FixedWindows,
    Seed,
    chapter_call,
    editor_script,
    review,
    text_of,
    writer_script,
)

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import Call, FakeAgent, Hang
from story_maker.agents.port import AgentPort
from story_maker.config import Config
from story_maker.lint.chapter import LINTERS
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Trace
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import ChapterProducer, Production
from story_maker.store.models import Attempt, Checkpoint, RoleSession, Run

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


async def test_rewriting_is_a_new_writer_session_with_the_defects_and_without_the_old_text(
    producer: ChapterProducer,
    fake: FakeAgent,
    windows: FixedWindows,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    first_text = text_of(1250, word="primera")
    low = review(
        {**dict.fromkeys(CRITERIA, 4), "fidelidad-canon": 2},
        defects=[{"criterion": "prosa", "blocking": False, "message": "repite «faro»"}],
    )
    fake.script("writer", "write", writer_script(chapter_call(text=first_text)))
    fake.script("editor", None, editor_script(low))
    fake.script("writer", "rewrite", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(review()))

    await producer.produce_chapter(seed.run_id, 4, trace)

    assert roles(fake) == [
        ("writer", "write"),
        ("editor", None),
        ("writer", "rewrite"),
        ("editor", None),
    ]
    first, second = message(fake, 0), message(fake, 2)
    assert second["window"] == first["window"]
    assert windows.writer_calls == [(seed.version_id, 4)]
    defects = [d for d in second["call_inputs"]["defects"] if d["validator"] not in LINTERS]
    assert [(d["criterion"], d["blocking"]) for d in defects] == [
        ("fidelidad-canon", True),
        ("prosa", False),
    ]
    # Los avisos de los linters citan la palabra repetida (018-C1, C21), nunca el texto.
    assert text_of(50, word="primera") not in fake.sessions[2].request.message
    assert fake.sessions[2].request.chapter_checks is not None
    assert [s.name for s in trace.scores].count("longitud-capitulo") == 2
    assert attempts(session_factory, seed.run_id, 4) == [(1, "rewrite"), (2, "accept")]


def set_chapter(session_factory: sessionmaker[Session], seed: Seed, chapter: int) -> None:
    """La ejecución de la fixture con los puntos de control 0 a chapter-1."""
    with session_factory() as session:
        run = session.get(Run, seed.run_id)
        assert run is not None
        run.chapter = chapter
        for k in range(1, chapter):
            session.add(Checkpoint(run_id=seed.run_id, chapter=k, created_at=NOW))
        session.commit()


async def test_three_attempts_rewrite_rewrite_accept_accept_the_chapter_in_the_third(
    producer: ChapterProducer,
    fake: FakeAgent,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    set_chapter(session_factory, seed, 5)
    low = review({**dict.fromkeys(CRITERIA, 4), "cumple-beats": 1})
    fake.script("writer", "write", writer_script(chapter_call()))
    fake.script("writer", "rewrite", writer_script(chapter_call()))
    fake.script("writer", "rewrite", writer_script(chapter_call()))
    for given in (low, low, review()):
        fake.script("editor", None, editor_script(given))

    await producer.produce_chapter(seed.run_id, 5, trace)

    assert attempts(session_factory, seed.run_id, 5) == [
        (1, "rewrite"),
        (2, "rewrite"),
        (3, "accept"),
    ]


EXHAUSTED = {
    "rewrite, rewrite y bloqueantes": "retries_exhausted",
    "tres prohibidas en la misma sesión": "banned_content",
    "prohibida, prohibida y 1.501": "retries_exhausted",
    "1.501, 1.501 y prohibida": "banned_content",
}


def script_exhaustion(fake: FakeAgent, row: str) -> None:
    banned = chapter_call(text=text_of(1249) + f" {BANNED}")
    long = chapter_call(1501)
    if row == "rewrite, rewrite y bloqueantes":
        low = review({**dict.fromkeys(CRITERIA, 4), "fidelidad-canon": 2})
        fake.script("writer", "write", writer_script(chapter_call()))
        fake.script("writer", "rewrite", writer_script(chapter_call()))
        fake.script("writer", "rewrite", writer_script(chapter_call()))
        for _ in range(3):
            fake.script("editor", None, editor_script(low))
        return
    calls = {
        "tres prohibidas en la misma sesión": (banned, banned, banned),
        "prohibida, prohibida y 1.501": (banned, banned, long),
        "1.501, 1.501 y prohibida": (long, long, banned),
    }[row]
    fake.script("writer", "write", writer_script(*calls, chapter_call()))


@pytest.mark.parametrize("row", list(EXHAUSTED))
async def test_the_attempts_of_a_chapter_run_out_with_a_reason_and_never_a_fourth(
    row: str,
    orchestrator: Orchestrator,
    fake: FakeAgent,
    seed: Seed,
    session_factory: sessionmaker[Session],
) -> None:
    set_chapter(session_factory, seed, 5)
    script_exhaustion(fake, row)

    await orchestrator.execute(seed.run_id)

    with session_factory() as session:
        run = session.get(Run, seed.run_id)
        assert run is not None
        assert (run.status, run.reason) == ("failed", EXHAUSTED[row])
        numbers = [n for n, _ in attempts(session_factory, seed.run_id, 5)]
        assert numbers == [1, 2, 3]
        assert [o for _, o in attempts(session_factory, seed.run_id, 5)][-1] == "fail"
        writers = session.query(RoleSession).filter_by(role="writer")
    if row != "rewrite, rewrite y bloqueantes":
        assert [s.request.role for s in fake.sessions] == ["writer"]
        assert [w.outcome for w in writers] == ["cut"]

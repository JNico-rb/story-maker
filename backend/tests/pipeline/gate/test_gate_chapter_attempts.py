"""012-C20 · Cada capítulo reescrito tiene sus intentos en cada ciclo.

Fixture del caso: `max_retries.chapter` = 1 (dos intentos por capítulo y ciclo)."""

from __future__ import annotations

import asyncio
import dataclasses

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    BANNED,
    Seed,
    chapter_call,
    editor_script,
    review,
    text_of,
    writer_script,
)
from tests.pipeline.gate.conftest import GateKit, evaluation, gate_passes, script_judges

from story_maker.agents.fake import FakeAgent
from story_maker.config import Config
from story_maker.observability.port import Trace
from story_maker.pipeline.runs import RunStop
from story_maker.store.models import Attempt

CITES_5 = evaluation({"continuidad": 2}, {"continuidad": (5,)})


@pytest.fixture
def config(config: Config) -> Config:
    return dataclasses.replace(config, max_retries={**config.max_retries, "chapter": 1})


def _rejected(fake: FakeAgent) -> None:
    fake.script("writer", "rewrite", writer_script(chapter_call(title="Rechazado")))
    fake.script("editor", None, editor_script(review(2)))


def _accepted(fake: FakeAgent) -> None:
    fake.script("writer", "rewrite", writer_script(chapter_call(title="Reescrito")))
    fake.script("editor", None, editor_script(review()))


def _chapter_attempts(
    session_factory: sessionmaker[Session], run_id: int
) -> list[tuple[int | None, int, str | None]]:
    with session_factory() as session:
        rows = session.query(Attempt).filter(
            Attempt.run_id == run_id, Attempt.evaluable == "chapter", Attempt.chapter == 5
        )
        return [(a.gate_cycle, a.number, a.outcome) for a in rows.order_by(Attempt.id)]


def test_two_rejections_of_a_rewritten_chapter_in_one_cycle_fail_with_retries_exhausted(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    script_judges(fake, CITES_5)
    _rejected(fake)
    _rejected(fake)

    with pytest.raises(RunStop) as stop:
        asyncio.run(kit.gate(at_gate.run_id, trace))

    assert (stop.value.status, stop.value.reason) == ("failed", "retries_exhausted")
    assert _chapter_attempts(session_factory, at_gate.run_id) == [(1, 1, "rewrite"), (1, 2, "fail")]


def test_a_last_rejection_for_a_banned_term_fails_with_banned_content(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    script_judges(fake, CITES_5)
    _rejected(fake)
    banned = chapter_call(text=f"{text_of(1249)} {BANNED}")
    fake.script("writer", "rewrite", writer_script(banned))

    with pytest.raises(RunStop) as stop:
        asyncio.run(kit.gate(at_gate.run_id, trace))

    assert (stop.value.status, stop.value.reason) == ("failed", "banned_content")


def test_a_chapter_attributed_again_in_the_next_cycle_gets_its_attempts_again(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    script_judges(fake, CITES_5, CITES_5, evaluation())
    for _ in range(2):
        _rejected(fake)
        _accepted(fake)

    asyncio.run(kit.gate(at_gate.run_id, trace))

    assert gate_passes(session_factory, at_gate.run_id) == [
        (1, "rewrite"),
        (2, "rewrite"),
        (3, "accept"),
    ]
    assert _chapter_attempts(session_factory, at_gate.run_id) == [
        (1, 1, "rewrite"),
        (1, 2, "accept"),
        (2, 1, "rewrite"),
        (2, 2, "accept"),
    ]

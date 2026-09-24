"""La sesión del writer: sus hooks, qué cuenta como intento y cuándo se abre el editor
(011-C10 a 011-C14)."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    FixedWindows,
    Seed,
    chapter_call,
    editor_script,
    review,
    text_of,
    writer_script,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Trace
from story_maker.pipeline.production import ChapterProducer
from story_maker.store.models import AuditLog, RoleSession, ValidatorResult


def _results(session: Session, run_id: int) -> list[tuple[str, bool, int]]:
    rows = session.query(ValidatorResult).filter_by(run_id=run_id).order_by(ValidatorResult.id)
    return [(r.validator, r.passed, r.detail["attempt"]) for r in rows]


async def test_a_delivery_that_passes_the_hooks_reaches_the_editor(
    producer: ChapterProducer,
    fake: FakeAgent,
    windows: FixedWindows,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    first = text_of(1250)
    second = text_of(1250, word="otra")
    fake.script(
        "writer",
        "write",
        writer_script(
            chapter_call(title="El faro", text=first), chapter_call(title="Otro", text=second)
        ),
    )
    fake.script("editor", None, editor_script(review()))

    await producer.produce_chapter(seed.run_id, 4, trace)

    with session_factory() as session:
        decisions = session.query(AuditLog).filter_by(role="writer", tool="submit_chapter")
        assert decisions.first() is not None
        assert decisions.first().decision == "allow"
        assert _results(session, seed.run_id)[:2] == [
            ("longitud-capitulo", True, 1),
            ("nombres-exactos", True, 1),
        ]
        writer = session.query(RoleSession).filter_by(role="writer").one()
        assert writer.outcome == "completed"
    assert windows.editor_calls == [(seed.version_id, 4, "El faro", first)]
    editor = fake.sessions[1]
    assert editor.request.role == "editor"
    inputs = json.loads(editor.request.message)["call_inputs"]
    assert (inputs["title"], inputs["text"]) == ("El faro", first)
    assert second not in editor.request.message

"""La sesión del writer: sus hooks, qué cuenta como intento y cuándo se abre el editor
(011-C10 a 011-C14)."""

from __future__ import annotations

import json

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    BANNED,
    FixedWindows,
    Seed,
    chapter_call,
    editor_script,
    review,
    text_of,
    writer_script,
)

from story_maker.agents.fake import Call, FakeAgent
from story_maker.agents.port import ACK
from story_maker.observability.port import Trace
from story_maker.pipeline.production import ChapterProducer
from story_maker.store.models import Attempt, AuditLog, RoleSession, ValidatorResult


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


def _attempts(session: Session, run_id: int, chapter: int) -> list[tuple[int, str | None]]:
    rows = session.query(Attempt).filter_by(run_id=run_id, chapter=chapter).order_by(Attempt.id)
    return [(a.number, a.outcome) for a in rows]


@pytest.mark.parametrize("words", [999, 1501])
async def test_a_length_out_of_range_blocks_counts_as_an_attempt_and_is_fixed_in_the_session(
    words: int,
    producer: ChapterProducer,
    fake: FakeAgent,
    windows: FixedWindows,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    good = text_of(1250)
    fake.script("writer", "write", writer_script(chapter_call(words), chapter_call(text=good)))
    fake.script("editor", None, editor_script(review()))

    await producer.produce_chapter(seed.run_id, 4, trace)

    writer = fake.sessions[0]
    shown = writer.reads[0]
    assert "[longitud-capitulo]" in shown
    assert f"{words:,}".replace(",", ".") in shown
    assert "1.000" in shown
    assert "1.500" in shown
    assert writer.reads[1] == ACK
    assert [s.request.role for s in fake.sessions] == ["writer", "editor"]
    assert [call[3] for call in windows.editor_calls] == [good]
    with session_factory() as session:
        assert _attempts(session, seed.run_id, 4) == [(1, "rewrite"), (2, "accept")]
        assert ("longitud-capitulo", False, 1) in _results(session, seed.run_id)


@pytest.mark.parametrize(
    ("title", "text"),
    [("El faro", text_of(1249) + " Tobi"), ("El faro de Tobi", text_of(1250))],
)
async def test_a_name_variant_in_the_title_or_the_text_blocks_like_a_length_defect(
    title: str,
    text: str,
    producer: ChapterProducer,
    fake: FakeAgent,
    windows: FixedWindows,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    good = text_of(1250)
    fake.script(
        "writer",
        "write",
        writer_script(chapter_call(title=title, text=text), chapter_call(text=good)),
    )
    fake.script("editor", None, editor_script(review()))

    await producer.produce_chapter(seed.run_id, 4, trace)

    shown = fake.sessions[0].reads[0]
    assert "[nombres-exactos] «Tobi» es una variante de «Toby»" in shown
    assert [s.request.role for s in fake.sessions] == ["writer", "editor"]
    assert [call[3] for call in windows.editor_calls] == [good]
    with session_factory() as session:
        assert _attempts(session, seed.run_id, 4) == [(1, "rewrite"), (2, "accept")]
        assert ("nombres-exactos", False, 1) in _results(session, seed.run_id)


BANNED_TEXT = text_of(1249) + f" {BANNED}"
COUNTING_CALLS = {
    "prohibida en el texto": chapter_call(text=BANNED_TEXT),
    "prohibida en el título": chapter_call(title=f"El {BANNED}"),
    "prohibida y 900 palabras": chapter_call(text=text_of(899) + f" {BANNED}"),
    "fuera de schema": Call("submit_chapter", {"title": "El faro"}),
    "1.501 palabras": chapter_call(1501),
}
FREE_CALLS = {
    "Skill admitida": Call("Skill", {"skill": "personalizacion-natural"}),
    "otra skill": Call("Skill", {"skill": "otra-skill"}),
    "tool fuera de la lista": Call("Bash", {"command": "dir"}),
}


@pytest.mark.parametrize("row", list(COUNTING_CALLS))
async def test_a_rejected_submit_chapter_counts_as_an_attempt_without_opening_the_editor(
    row: str,
    producer: ChapterProducer,
    fake: FakeAgent,
    windows: FixedWindows,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    good = text_of(1250)
    fake.script("writer", "write", writer_script(COUNTING_CALLS[row], chapter_call(text=good)))
    fake.script("editor", None, editor_script(review()))

    await producer.produce_chapter(seed.run_id, 4, trace)

    assert [s.request.role for s in fake.sessions] == ["writer", "editor"]
    assert [call[3] for call in windows.editor_calls] == [good]
    with session_factory() as session:
        assert _attempts(session, seed.run_id, 4) == [(1, "rewrite"), (2, "accept")]
        first_attempt = [r for r in _results(session, seed.run_id) if r[2] == 1]
    shown = fake.sessions[0].reads[0]
    if "prohibida" in row:
        assert shown.startswith("palabras-prohibidas")
        assert BANNED in shown
        assert first_attempt == []  # ni el schema ni el hook de validación corrieron
    elif row == "fuera de schema":
        assert shown.startswith("Entrada inválida para submit_chapter")
        assert first_attempt == []
    else:
        assert "[longitud-capitulo]" in shown


@pytest.mark.parametrize("row", list(FREE_CALLS))
async def test_other_tool_calls_do_not_count_as_attempts(
    row: str,
    producer: ChapterProducer,
    fake: FakeAgent,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    fake.script("writer", "write", writer_script(FREE_CALLS[row], chapter_call()))
    fake.script("editor", None, editor_script(review()))

    await producer.produce_chapter(seed.run_id, 4, trace)

    allowed = row == "Skill admitida"
    assert fake.sessions[0].reads[0] == "Hecho." if allowed else fake.sessions[0].reads[0] != ACK
    with session_factory() as session:
        assert _attempts(session, seed.run_id, 4) == [(1, "accept")]

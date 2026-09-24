"""Writer y editor son sesiones distintas y el editor no recibe nada del writer (011-I8)."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    USAGE,
    Seed,
    chapter_call,
    editor_script,
    review,
    text_of,
)

from story_maker.agents.fake import FakeAgent, Say, Script
from story_maker.agents.profiles import whitelist
from story_maker.observability.port import Trace
from story_maker.pipeline.production import ChapterProducer

REASONING = "razonamiento-privado-del-writer"
REJECTED = "entregarechazada"


async def test_writer_and_editor_are_distinct_sessions_and_the_editor_gets_nothing_of_the_writer(
    producer: ChapterProducer,
    fake: FakeAgent,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    short = chapter_call(text=text_of(400, word=REJECTED))
    fake.script(
        "writer",
        "write",
        Script(steps=(short, chapter_call(), Say(REASONING)), usage=USAGE),
    )
    fake.script("editor", None, editor_script(review()))

    await producer.produce_chapter(seed.run_id, 1, trace)

    writer, editor = fake.sessions
    assert writer is not editor
    assert (writer.request.role, editor.request.role) == ("writer", "editor")
    assert [t.name for t in writer.request.tools] == ["submit_chapter"]
    assert [t.name for t in editor.request.tools] == ["submit_review"]
    assert set(whitelist("writer", "write")) == {"submit_chapter", "Skill"}
    assert set(whitelist("editor", None)) == {"submit_review", "Skill"}
    assert "submit_chapter" not in editor.profile.own_tools
    message = editor.request.message
    assert REASONING not in message
    assert REJECTED not in message
    assert "longitud-capitulo" not in message

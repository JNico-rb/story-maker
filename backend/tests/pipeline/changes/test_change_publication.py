"""014-C15 · Superado el gate, se publica la versión nueva y la solicitud pasa a `applied`
(y 014-I7 en la rama que publica)."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.changes.conftest import (
    V1,
    confirm,
    new_trait,
    rename_toby,
    request_of,
    run_of,
    script_judge,
    v1_text,
    version_fingerprint,
    versions,
)
from tests.pipeline.conftest import chapter_call, editor_script, review, writer_script

from story_maker.agents.fake import FakeAgent
from story_maker.pipeline.worker import Worker
from story_maker.store.versions import current_version


def _revise(fake: FakeAgent, chapter: int, *, identical: bool = False) -> None:
    call = (
        chapter_call(title=f"Capítulo {chapter}", text=v1_text(chapter))
        if identical
        else chapter_call(title=f"Revisado {chapter}")
    )
    fake.script("writer", "revise", writer_script(call))
    fake.script("editor", None, editor_script(review()))


async def test_passing_the_gate_publishes_v2_over_v1_and_applies_the_request(
    session_factory: sessionmaker[Session], v1: V1, fake: FakeAgent, worker: Worker
) -> None:
    confirmed = confirm(session_factory, v1.novel_id, v1.v1_id, rename_toby(v1))
    before = version_fingerprint(session_factory, v1.v1_id)
    for chapter in (2, 5, 7):
        _revise(fake, chapter)
    script_judge(fake)

    assert await worker.run_next() == confirmed.run_id

    run = run_of(session_factory, confirmed.run_id)
    assert run.status == "published"
    assert request_of(session_factory, confirmed.request_id).status == "applied"
    base, new = versions(session_factory, v1.novel_id)
    assert (new.id, new.status, new.number, new.base_version_id) == (
        run.candidate_version_id,
        "published",
        2,
        v1.v1_id,
    )
    assert list(new.changed_chapters) == [2, 5, 7]
    assert base.status == "published"
    assert version_fingerprint(session_factory, v1.v1_id) == before
    with session_factory() as session:
        current = current_version(session, v1.novel_id)
        assert current is not None
        assert current.id == new.id


async def test_an_affected_chapter_returned_identical_is_not_changed(
    session_factory: sessionmaker[Session], v1: V1, fake: FakeAgent, worker: Worker
) -> None:
    confirm(session_factory, v1.novel_id, v1.v1_id, rename_toby(v1))
    _revise(fake, 2)
    _revise(fake, 5, identical=True)
    _revise(fake, 7)
    script_judge(fake)

    await worker.run_next()

    new = versions(session_factory, v1.novel_id)[-1]
    assert (new.number, list(new.changed_chapters)) == (2, [2, 7])


async def test_without_affected_chapters_no_writer_opens_and_v2_has_no_changed_chapters(
    session_factory: sessionmaker[Session], v1: V1, fake: FakeAgent, worker: Worker
) -> None:
    confirmed = confirm(session_factory, v1.novel_id, v1.v1_id, new_trait(v1))
    script_judge(fake)

    await worker.run_next()

    assert run_of(session_factory, confirmed.run_id).status == "published"
    assert not [s for s in fake.sessions if s.request.role in ("writer", "editor")]
    new = versions(session_factory, v1.novel_id)[-1]
    assert (new.number, list(new.changed_chapters)) == (2, [])

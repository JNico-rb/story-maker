"""014-C16 · La reescritura dirigida del gate puede tocar un capítulo no afectado."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.changes.conftest import (
    V1,
    confirm,
    rename_toby,
    run_of,
    script_judge,
    script_revisions,
    versions,
)
from tests.pipeline.gate.conftest import evaluation, gate_passes, script_rewrites

from story_maker.agents.fake import FakeAgent
from story_maker.pipeline.worker import Worker


async def test_the_gate_targeted_rewrite_can_touch_a_chapter_that_is_not_affected(
    session_factory: sessionmaker[Session], v1: V1, fake: FakeAgent, worker: Worker
) -> None:
    confirmed = confirm(session_factory, v1.novel_id, v1.v1_id, rename_toby(v1))
    script_revisions(fake, 3)
    script_judge(fake, evaluation({"continuidad": 2}, {"continuidad": (4,)}), evaluation())
    script_rewrites(fake, 1)

    await worker.run_next()

    assert run_of(session_factory, confirmed.run_id).status == "published"
    writers = [s.request for s in fake.sessions if s.request.role == "writer"]
    assert [(w.chapter, w.mode) for w in writers] == [
        (2, "revise"),
        (5, "revise"),
        (7, "revise"),
        (4, "rewrite"),
    ]
    assert gate_passes(session_factory, confirmed.run_id) == [(1, "rewrite"), (2, "accept")]
    new = versions(session_factory, v1.novel_id)[-1]
    assert (new.number, list(new.changed_chapters)) == (2, [2, 4, 5, 7])

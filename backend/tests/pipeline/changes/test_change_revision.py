"""014-C14 · Solo los afectados pasan por el writer, en orden y en modo revisión."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.changes.conftest import (
    V1,
    checkpoints,
    confirm,
    rename_toby,
    run_of,
    script_judge,
    v1_text,
    versions,
)
from tests.pipeline.conftest import (
    CRITERIA,
    FixedWindows,
    chapter_call,
    editor_script,
    review,
    writer_script,
)
from tests.pipeline.gate.conftest import chapter_hashes

from story_maker.agents.fake import FakeAgent
from story_maker.lint.chapter import LINTERS
from story_maker.pipeline.changes.run import REVISE_INSTRUCTION
from story_maker.pipeline.worker import Worker

CHANGE = {
    "changed_facts": [
        {"subject": "Toby", "attribute": "name", "old_value": "Toby", "new_value": "Nala"}
    ],
    "new_fact": None,
}


def _inputs(message: str) -> dict[str, Any]:
    inputs: dict[str, Any] = json.loads(message)["call_inputs"]
    return inputs


async def test_only_the_affected_chapters_are_revised_in_order_with_the_change_and_the_loop(
    session_factory: sessionmaker[Session],
    v1: V1,
    fake: FakeAgent,
    worker: Worker,
    windows: FixedWindows,
) -> None:
    confirmed = confirm(session_factory, v1.novel_id, v1.v1_id, rename_toby(v1))
    low = review({**dict.fromkeys(CRITERIA, 4), "fidelidad-canon": 2})
    for chapter in (2, 5, 7):
        fake.script("writer", "revise", writer_script(chapter_call(title=f"Revisado {chapter}")))
        if chapter == 5:
            fake.script("editor", None, editor_script(low))
            fake.script("writer", "revise", writer_script(chapter_call(title="Revisado 5 bis")))
        fake.script("editor", None, editor_script(review()))
    script_judge(fake)

    assert await worker.run_next() == confirmed.run_id

    run = run_of(session_factory, confirmed.run_id)
    assert run.status == "published"
    candidate_id = run.candidate_version_id
    assert [c for _, c in windows.writer_calls] == [2, 5, 7]
    assert {v for v, _ in windows.writer_calls} == {candidate_id}
    writers = [s.request for s in fake.sessions if s.request.role == "writer"]
    editors = [s.request for s in fake.sessions if s.request.role == "editor"]
    assert [(w.chapter, w.mode) for w in writers] == [
        (2, "revise"),
        (5, "revise"),
        (5, "revise"),
        (7, "revise"),
    ]
    assert [e.chapter for e in editors] == [2, 5, 5, 7]
    for request in writers:
        inputs = _inputs(request.message)
        assert inputs["chapter"] == {
            "title": f"Capítulo {request.chapter}",
            "text": v1_text(request.chapter or 0),
        }
        assert inputs["change"] == CHANGE
        assert inputs["instruction"] == REVISE_INSTRUCTION
    assert "defects" not in _inputs(writers[1].message)
    defects = [d for d in _inputs(writers[2].message)["defects"] if d["validator"] not in LINTERS]
    assert [d["criterion"] for d in defects] == ["fidelidad-canon"]
    assert all(_inputs(e.message)["change"] == CHANGE for e in editors)
    assert checkpoints(session_factory, confirmed.run_id) == [0, 2, 5, 7]
    base, new = (
        chapter_hashes(session_factory, v1.v1_id),
        chapter_hashes(session_factory, candidate_id or 0),
    )
    assert {n for n in base if base[n] == new[n]} == {1, 3, 4, 6, 8, 9, 10}
    assert len(versions(session_factory, v1.novel_id)) == 2

"""019-C26 y 019-C27 · Una base obsoleta al arrancar o al relanzarse termina en `stale_base` con la
edición `rejected`; reanudar una edición sigue por lo que quedaba, sin repetir el capítulo
editado."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.changes.conftest import (
    CrashingWindows,
    change,
    checkpoints,
    confirm,
    crash_and_restart,
    request_of,
    resume,
)
from tests.pipeline.conftest import chapter_call, editor_script, review, writer_script
from tests.pipeline.gate.conftest import evaluation, judge_script
from tests.pipeline.manual_edit.conftest import N, clean_text
from tests.pipeline.manual_edit.test_edit_run import (
    attempts,
    candidate_fact,
    chapter_of,
    edit_of,
    edited_review,
    published,
    queue_edit,
    rename_review,
    renamed,
    rewritten_text,
    roles,
    run_of,
    script_revisions,
)

from story_maker.agents.fake import FakeAgent
from story_maker.pipeline.report import build_report
from story_maker.pipeline.worker import Worker
from story_maker.store.models import Fact, FactUsage, Run, Version


@pytest.fixture
def windows() -> CrashingWindows:
    return CrashingWindows()


def _stale_report(session_factory: sessionmaker[Session], run_id: int) -> dict[str, Any]:
    with session_factory() as session:
        return build_report(session, session.get_one(Run, run_id))


def assert_stale(session_factory: sessionmaker[Session], n: N, run_id: int) -> None:
    run = run_of(session_factory, run_id)
    assert (run.status, run.reason) == ("failed", "stale_base")
    assert edit_of(session_factory, run_id).status == "rejected"
    report = _stale_report(session_factory, run_id)
    assert report["reason"] == "stale_base"
    assert "ya no es la vigente" in report["reason_detail"]
    with session_factory() as session:
        rows = session.query(Version).filter_by(novel_id=n.novel_id, status="published")
        assert sorted(v.number for v in rows) == [1, 2]


async def test_of_two_edits_over_v1_the_second_fails_with_stale_base_before_its_candidate(
    n: N, fake: FakeAgent, worker: Worker, session_factory: sessionmaker[Session]
) -> None:
    first = queue_edit(session_factory, n, rewritten_text(session_factory, n))
    second = queue_edit(session_factory, n, clean_text(9), chapter=5)
    fake.script("editor", None, editor_script(edited_review(session_factory, n)))
    fake.script("judge", None, judge_script(evaluation(4)))

    assert await worker.run_next() == first
    assert await worker.run_next() == second

    assert run_of(session_factory, first).status == "published"
    assert edit_of(session_factory, first).status == "applied"
    assert_stale(session_factory, n, second)
    assert run_of(session_factory, second).candidate_version_id is None
    assert roles(fake) == [("editor", 3), ("judge", None)]


async def test_an_edit_over_v1_after_a_confirmed_change_over_v1_fails_with_stale_base(
    n: N, fake: FakeAgent, worker: Worker, session_factory: sessionmaker[Session]
) -> None:
    confirmed = confirm(session_factory, n.novel_id, n.v1_id, change(n.toby_name, "Toby", "Nala"))
    edit = queue_edit(session_factory, n, rewritten_text(session_factory, n))
    for revised in (review(), edited_review(session_factory, n), review()):
        fake.script("writer", "revise", writer_script(chapter_call(title="Revisado")))
        fake.script("editor", None, editor_script(revised))
    fake.script("judge", None, judge_script(evaluation(4)))

    assert await worker.run_next() == confirmed.run_id
    assert await worker.run_next() == edit

    assert request_of(session_factory, confirmed.request_id).status == "applied"
    assert_stale(session_factory, n, edit)
    assert run_of(session_factory, edit).candidate_version_id is None


async def test_resuming_an_edit_after_its_chapter_goes_on_with_chapter_1_without_repeating_it(
    n: N,
    fake: FakeAgent,
    worker: Worker,
    windows: CrashingWindows,
    session_factory: sessionmaker[Session],
) -> None:
    text = renamed(session_factory, n)
    run_id = queue_edit(session_factory, n, text)
    toby_name = candidate_fact(session_factory, n.toby_name, n)
    fake.script("editor", None, editor_script(rename_review(session_factory, n)))
    script_revisions(fake, 2)
    fake.script("judge", None, judge_script(evaluation(4)))
    windows.crash_at = 1

    await crash_and_restart(worker)

    run = run_of(session_factory, run_id)
    assert (run.status, run.reason) == ("interrupted", "crash")
    assert checkpoints(session_factory, run_id) == [0, 3]
    assert edit_of(session_factory, run_id).status == "queued"
    resume(session_factory, run_id)
    assert await worker.run_next() == run_id

    assert run_of(session_factory, run_id).status == "published"
    assert roles(fake) == [
        ("editor", 3),
        ("writer", 1),
        ("editor", 1),
        ("writer", 7),
        ("editor", 7),
        ("judge", None),
    ]
    assert attempts(session_factory, run_id, 3) == [(1, "accept")]
    v2 = published(session_factory, n, 2)
    assert v2.changed_chapters == [1, 3, 7]
    assert chapter_of(session_factory, v2.id, 3).text == text
    with session_factory() as session:
        assert session.get_one(Fact, toby_name).value == "Nala"
        assert session.query(FactUsage).filter_by(fact_id=toby_name, chapter=3).count() == 1
    assert edit_of(session_factory, run_id).status == "applied"


async def test_an_interrupted_edit_resumed_after_another_published_v2_fails_with_stale_base(
    n: N,
    fake: FakeAgent,
    worker: Worker,
    windows: CrashingWindows,
    session_factory: sessionmaker[Session],
) -> None:
    first = queue_edit(session_factory, n, renamed(session_factory, n))
    other = queue_edit(session_factory, n, clean_text(9), chapter=5)
    fake.script("editor", None, editor_script(rename_review(session_factory, n)))
    fake.script("editor", None, editor_script(review()))
    fake.script("judge", None, judge_script(evaluation(4)))
    windows.crash_at = 1

    await crash_and_restart(worker)

    assert run_of(session_factory, first).status == "interrupted"
    assert edit_of(session_factory, first).status == "queued"
    assert await worker.run_next() == other
    assert run_of(session_factory, other).status == "published"
    assert edit_of(session_factory, first).status == "queued"

    resume(session_factory, first)
    assert await worker.run_next() == first

    assert_stale(session_factory, n, first)
    with session_factory() as session:
        candidate = session.get_one(Run, first).candidate_version_id
        assert session.get_one(Version, candidate).status == "discarded"
    assert not any(s.request.role == "writer" for s in fake.sessions)

"""014-C19 · La ejecución de cambio tiene su traza `solicitud-de-cambio` en la sesión de la novela,
la conserva al reanudarse y solo lleva spans `capitulo-<n>` de lo que reescribió. La traza de la
propuesta está en `tests/api/change_requests/test_c19_proposal_trace.py`."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.changes.conftest import (
    V1,
    CrashingWindows,
    confirm,
    crash_and_restart,
    rename_toby,
    resume,
    run_of,
    script_judge,
    script_revisions,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Trace
from story_maker.pipeline.worker import Worker


def _chapter_spans(trace: Trace) -> list[str]:
    return [s.name for s in trace.spans if s.name.startswith("capitulo-")]


async def test_a_change_run_has_its_trace_in_the_novel_session_with_only_the_rewritten_chapters(
    session_factory: sessionmaker[Session],
    v1: V1,
    fake: FakeAgent,
    worker: Worker,
    telemetry: NullObservability,
) -> None:
    confirmed = confirm(session_factory, v1.novel_id, v1.v1_id, rename_toby(v1))
    script_revisions(fake, 3)
    script_judge(fake)

    await worker.run_next()

    assert run_of(session_factory, confirmed.run_id).status == "published"
    trace = telemetry.traces[f"run:{confirmed.run_id}"]
    assert (trace.name, trace.session) == ("solicitud-de-cambio", str(v1.novel_id))
    assert _chapter_spans(trace) == ["capitulo-2", "capitulo-5", "capitulo-7"]


async def test_resuming_a_change_run_keeps_its_one_trace(
    session_factory: sessionmaker[Session],
    v1: V1,
    fake: FakeAgent,
    worker: Worker,
    windows: CrashingWindows,
    telemetry: NullObservability,
) -> None:
    confirmed = confirm(session_factory, v1.novel_id, v1.v1_id, rename_toby(v1))
    windows.crash_at = 7
    script_revisions(fake, 3)
    script_judge(fake)
    await crash_and_restart(worker)
    before = telemetry.traces[f"run:{confirmed.run_id}"]

    resume(session_factory, confirmed.run_id)
    await worker.run_next()

    assert run_of(session_factory, confirmed.run_id).status == "published"
    changes = [t for t in telemetry.traces.values() if t.name == "solicitud-de-cambio"]
    assert changes == [before]
    assert before.session == str(v1.novel_id)
    assert set(_chapter_spans(before)) == {"capitulo-2", "capitulo-5", "capitulo-7"}

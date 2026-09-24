"""014-C18 · Reanudar una ejecución de cambio revalida la base y sigue por el siguiente afectado
(y 014-I10). La caída dentro de la transacción de 014-C13 está en `test_change_candidate.py`."""

from __future__ import annotations

import dataclasses

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.changes.conftest import (
    V1,
    CrashingWindows,
    ServerStopped,
    checkpoints,
    confirm,
    crash_and_restart,
    new_trait,
    rename_toby,
    request_of,
    resume,
    run_of,
    script_judge,
    script_revisions,
    versions,
)
from tests.pipeline.gate.conftest import GateKit, PdfDouble, evaluation

from story_maker.agents.fake import FakeAgent
from story_maker.pipeline.gate.phase import PdfOutcome
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import Production
from story_maker.pipeline.worker import Worker


@dataclasses.dataclass
class CrashingPdf:
    """El PDF del kit; la primera llamada detiene el servidor."""

    inner: PdfDouble
    crashed: bool = False

    async def __call__(self, version_id: int) -> PdfOutcome:
        if not self.crashed:
            self.crashed = True
            raise ServerStopped
        return await self.inner(version_id)


def _writers(fake: FakeAgent) -> list[int | None]:
    return [s.request.chapter for s in fake.sessions if s.request.role == "writer"]


async def test_resuming_after_chapter_5_revalidates_and_goes_on_with_chapter_7_only(
    session_factory: sessionmaker[Session],
    v1: V1,
    fake: FakeAgent,
    worker: Worker,
    windows: CrashingWindows,
) -> None:
    confirmed = confirm(session_factory, v1.novel_id, v1.v1_id, rename_toby(v1))
    windows.crash_at = 7
    script_revisions(fake, 3)
    script_judge(fake)

    await crash_and_restart(worker)

    run = run_of(session_factory, confirmed.run_id)
    assert (run.status, run.reason) == ("interrupted", "crash")
    assert checkpoints(session_factory, confirmed.run_id) == [0, 2, 5]
    assert request_of(session_factory, confirmed.request_id).status == "confirmed"
    assert _writers(fake) == [2, 5]

    resume(session_factory, confirmed.run_id)
    assert await worker.run_next() == confirmed.run_id

    assert _writers(fake) == [2, 5, 7]
    assert checkpoints(session_factory, confirmed.run_id) == [0, 2, 5, 7]
    assert run_of(session_factory, confirmed.run_id).status == "published"
    assert request_of(session_factory, confirmed.request_id).status == "applied"
    new = versions(session_factory, v1.novel_id)[-1]
    assert (new.number, list(new.changed_chapters)) == (2, [2, 5, 7])


async def test_resuming_after_a_crash_in_the_gate_repeats_the_gate_on_the_candidate_as_left(
    session_factory: sessionmaker[Session],
    v1: V1,
    fake: FakeAgent,
    kit: GateKit,
    production: Production,
    orchestrator: Orchestrator,
) -> None:
    gate = dataclasses.replace(kit.gate, pdf=CrashingPdf(kit.pdf))
    orchestrator = dataclasses.replace(orchestrator, gate=gate)
    worker = Worker(
        production.session_factory,
        orchestrator.execute,
        max_resumes=production.config.max_resumes,
        clock=production.clock,
    )
    confirmed = confirm(session_factory, v1.novel_id, v1.v1_id, rename_toby(v1))
    script_revisions(fake, 3)
    script_judge(fake, evaluation(), evaluation())

    await crash_and_restart(worker)

    run = run_of(session_factory, confirmed.run_id)
    assert (run.status, run.reason, run.phase) == ("interrupted", "crash", "gate")
    resume(session_factory, confirmed.run_id)
    assert await worker.run_next() == confirmed.run_id

    assert _writers(fake) == [2, 5, 7]
    assert [s.request.role for s in fake.sessions].count("judge") == 2
    assert checkpoints(session_factory, confirmed.run_id) == [0, 2, 5, 7]
    assert run_of(session_factory, confirmed.run_id).status == "published"
    new = versions(session_factory, v1.novel_id)[-1]
    assert (new.number, list(new.changed_chapters)) == (2, [2, 5, 7])


async def test_resuming_after_another_request_published_v2_fails_with_stale_base(
    session_factory: sessionmaker[Session],
    v1: V1,
    fake: FakeAgent,
    worker: Worker,
    windows: CrashingWindows,
) -> None:
    first = confirm(session_factory, v1.novel_id, v1.v1_id, rename_toby(v1))
    other = confirm(session_factory, v1.novel_id, v1.v1_id, new_trait(v1))
    windows.crash_at = 5
    script_revisions(fake, 1)

    await crash_and_restart(worker)

    assert run_of(session_factory, first.run_id).status == "interrupted"
    script_judge(fake)
    assert await worker.run_next() == other.run_id
    assert request_of(session_factory, first.request_id).status == "confirmed"
    v2 = versions(session_factory, v1.novel_id)[-1]
    assert (v2.status, v2.number) == ("published", 2)

    resume(session_factory, first.run_id)
    assert await worker.run_next() == first.run_id

    run = run_of(session_factory, first.run_id)
    assert (run.status, run.reason) == ("failed", "stale_base")
    assert request_of(session_factory, first.request_id).status == "rejected"
    by_id = {v.id: v for v in versions(session_factory, v1.novel_id)}
    assert by_id[run.candidate_version_id or 0].status == "discarded"
    assert _writers(fake) == [2]

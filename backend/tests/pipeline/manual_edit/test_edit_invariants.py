"""Invariantes de 019 que no cubre por sí sola una prueba de caso: el lint en vivo no escribe y es
determinista (019-I2), lo que marca como bloqueante es lo que bloquea el guardado (019-I3), sin
el resultado de `cronologia-lean` no se publica (019-I6) y la `EdicionManual` sigue `queued`
mientras su ejecución está en curso (019-I11)."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.changes.conftest import version_fingerprint
from tests.pipeline.conftest import editor_script
from tests.pipeline.gate.conftest import GateKit, LeanDouble, evaluation, judge_script
from tests.pipeline.manual_edit.conftest import INSULT, N, chapter_text
from tests.pipeline.manual_edit.test_edit_run import (
    edit_of,
    edited_review,
    queue_edit,
    rewritten_text,
    run_of,
)
from tests.pipeline.manual_edit.test_live_lint import AGES, lint, table_counts, with_lead
from tests.pipeline.manual_edit.test_save import save

from story_maker.agents.fake import FakeAgent
from story_maker.formal.candidate import CandidateVerification
from story_maker.formal.result import VerifierInterruption
from story_maker.observability.null import NullObservability
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import Production
from story_maker.pipeline.worker import Worker
from story_maker.store.models import ManualEdit, Run, Version

LEADS = (
    "Luego Tobi corrió. Ayer TOBY durmió.",
    "Luego vio a Pepe junto al faro.",
    f"Luego vio Tabacos y Jórge junto al {INSULT} del mar.",
    "Luego la ventana crujió. La ventana cayó. La ventana calló. Sin lugar a dudas llovía.",
    "Luego Rosa vio a Luis con Ana y Pablo. Ayer Rosa volvió.",
    AGES,
    "Luego Tobi vino.",
)


def lint_texts(session_factory: sessionmaker[Session], n: N) -> list[str]:
    """Los textos de 019-C02 a 019-C08, 019-C12 y 019-C14 sobre el capítulo 3."""
    third = chapter_text(session_factory, n.v1_id, 3)
    return [
        *(with_lead(session_factory, n, lead) for lead in LEADS),
        third.replace("Toby", "Nala"),
        third.replace("Toby", "Tobi"),
    ]


def lint_body(client: TestClient, n: N, text: str) -> list[dict[str, Any]]:
    response = lint(client, n, 3, text)
    assert response.status_code == 200, response.text
    return list(response.json()["diagnostics"])


def test_the_live_lint_writes_nothing_and_gives_the_same_diagnostics_twice(
    client: TestClient,
    n: N,
    telemetry: NullObservability,
    session_factory: sessionmaker[Session],
) -> None:
    texts = lint_texts(session_factory, n)
    counts, v1 = table_counts(session_factory), version_fingerprint(session_factory, n.v1_id)

    first = [lint_body(client, n, text) for text in texts]
    second = [lint_body(client, n, text) for text in texts]

    assert first == second
    assert all(first)
    assert table_counts(session_factory) == counts
    assert version_fingerprint(session_factory, n.v1_id) == v1
    assert telemetry.traces == {}


def _spots(diagnostics: list[dict[str, Any]]) -> set[tuple[str, int, int]]:
    return {(d["type"], d["position"]["start"], d["position"]["end"]) for d in diagnostics}


def test_what_the_lint_marks_as_blocking_is_exactly_what_the_save_rejects(
    client: TestClient, n: N, session_factory: sessionmaker[Session]
) -> None:
    statuses = []
    for text in lint_texts(session_factory, n):
        blocking = [d for d in lint_body(client, n, text) if d["blocking"]]

        response = save(client, n, 3, text)

        statuses.append(response.status_code)
        if not blocking:
            assert response.status_code == 202, response.text
            continue
        assert response.status_code == 422, response.text
        rejected = response.json()["detail"]["diagnostics"]
        assert {d["validator"] for d in rejected} <= {"palabras-prohibidas", "nombres-exactos"}
        assert _spots(rejected) == _spots(blocking)
    assert statuses.count(202) == 5
    assert statuses.count(422) == 4


async def test_without_the_lean_result_the_edit_is_not_published(
    n: N, fake: FakeAgent, worker: Worker, kit: GateKit, session_factory: sessionmaker[Session]
) -> None:
    run_id = queue_edit(session_factory, n, rewritten_text(session_factory, n))
    kit.lean.outcomes.append(VerifierInterruption("verifier_unreachable"))
    fake.script("editor", None, editor_script(edited_review(session_factory, n)))
    fake.script("judge", None, judge_script(evaluation(4)))

    await worker.run_next()

    run = run_of(session_factory, run_id)
    assert (run.status, run.reason) == ("interrupted", "verifier_unreachable")
    assert kit.pdf.calls == []
    assert edit_of(session_factory, run_id).status == "queued"
    with session_factory() as session:
        published = session.query(Version).filter_by(novel_id=n.novel_id, status="published")
        assert [v.id for v in published] == [n.v1_id]


@dataclass
class StatusSpy:
    """El doble de Lean del kit, que anota el estado de la ejecución y de la edición al correr."""

    inner: LeanDouble
    seen: list[tuple[str, str]] = field(default_factory=list)

    async def __call__(self, run_id: int) -> CandidateVerification:
        with self.inner.session_factory() as session:
            run = session.get_one(Run, run_id)
            edit = session.query(ManualEdit).filter_by(run_id=run_id).one()
            self.seen.append((run.status, edit.status))
        return await self.inner(run_id)


async def test_the_edit_stays_queued_while_its_run_is_running_and_is_applied_on_publishing(
    n: N,
    fake: FakeAgent,
    kit: GateKit,
    production: Production,
    orchestrator: Orchestrator,
    session_factory: sessionmaker[Session],
) -> None:
    run_id = queue_edit(session_factory, n, rewritten_text(session_factory, n))
    assert edit_of(session_factory, run_id).status == "queued"
    spy = StatusSpy(kit.lean)
    gate = dataclasses.replace(kit.gate, lean=spy)
    worker = Worker(
        session_factory,
        dataclasses.replace(orchestrator, gate=gate).execute,
        max_resumes=production.config.max_resumes,
        clock=production.clock,
    )
    fake.script("editor", None, editor_script(edited_review(session_factory, n)))
    fake.script("judge", None, judge_script(evaluation(4)))

    await worker.run_next()

    assert spy.seen == [("running", "queued")]
    assert run_of(session_factory, run_id).status == "published"
    assert edit_of(session_factory, run_id).status == "applied"

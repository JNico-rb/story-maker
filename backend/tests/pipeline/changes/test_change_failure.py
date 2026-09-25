"""014-C17 · Si la ejecución de cambio falla, la solicitud queda `rejected` y la base intacta
(y 014-I7 en la rama que falla)."""

from __future__ import annotations

import dataclasses
import datetime as dt

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.changes.conftest import (
    confirm,
    publish_v1,
    rename_toby,
    request_of,
    run_of,
    script_judge,
    script_revisions,
    version_fingerprint,
    versions,
)
from tests.pipeline.conftest import (
    BANNED,
    CRITERIA,
    Seed,
    chapter_call,
    editor_script,
    review,
    text_of,
    writer_script,
)
from tests.pipeline.gate.conftest import GateKit, LeanDouble

from story_maker.agents.fake import Fail, FakeAgent, Script
from story_maker.formal.candidate import CandidateVerification
from story_maker.formal.result import INVARIANTS, ChronologyResult
from story_maker.pipeline.gate.phase import PdfOutcome
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import Production
from story_maker.pipeline.worker import Worker
from story_maker.store.models import Event, Run
from story_maker.store.session import unit_of_work
from story_maker.store.versions import current_version

BRIEF_EVENTS = ("Marta adopta a Toby", "Toby llega al faro")


@dataclasses.dataclass
class BriefWitnessLean:
    """Lean con un testigo de T1 hecho solo de eventos del brief de la candidata."""

    inner: LeanDouble

    async def __call__(self, run_id: int) -> CandidateVerification:
        with self.inner.session_factory() as session:
            candidate = session.get_one(Run, run_id).candidate_version_id
            rows = session.query(Event.id).filter(
                Event.version_id == candidate, Event.origin == "brief"
            )
            before, after = (row[0] for row in rows.order_by(Event.id))
        holds = {t: t != "T1" for t in INVARIANTS}
        self.inner.outcomes.append(ChronologyResult("failed", holds, {"T1": (before, after)}))
        return await self.inner(run_id)


def _seed_brief_events(session_factory: sessionmaker[Session], seed: Seed) -> None:
    """En la candidata que será v1: el testigo tiene que ser suyo desde antes de publicarla."""
    with unit_of_work(session_factory) as uow:
        for day, statement in enumerate(BRIEF_EVENTS, start=1):
            uow.add(
                Event(
                    version_id=seed.version_id,
                    statement=statement,
                    moment=dt.datetime(2026, 4, day, 10, 0),
                    place_id=seed.places["Faro de Cabo Mayor"],
                    type="ordinary",
                    analepsis=False,
                    origin="brief",
                    chapter=None,
                    beat=None,
                )
            )


def _worker(production: Production, orchestrator: Orchestrator) -> Worker:
    return Worker(
        production.session_factory,
        orchestrator.execute,
        max_resumes=production.config.max_resumes,
        clock=production.clock,
    )


FAILURES = {
    "un revisado agota sus intentos con bloqueantes": "retries_exhausted",
    "un revisado agota sus intentos por una prohibida": "banned_content",
    "testigo Lean con solo eventos del brief": "unattributable_defect",
    "fallo de render": "render_failure",
    "interrumpida con max_resumes agotado": "resumes_exhausted",
}


@pytest.mark.parametrize("cause", list(FAILURES))
async def test_a_failed_change_run_rejects_the_request_and_leaves_the_base_intact(
    cause: str,
    session_factory: sessionmaker[Session],
    seed: Seed,
    fake: FakeAgent,
    kit: GateKit,
    production: Production,
    orchestrator: Orchestrator,
) -> None:
    if cause == "testigo Lean con solo eventos del brief":
        _seed_brief_events(session_factory, seed)
        gate = dataclasses.replace(kit.gate, lean=BriefWitnessLean(kit.lean))
        orchestrator = dataclasses.replace(orchestrator, gate=gate)
    v1 = publish_v1(session_factory, seed)
    confirmed = confirm(session_factory, v1.novel_id, v1.v1_id, rename_toby(v1))
    before = version_fingerprint(session_factory, v1.v1_id)
    if cause == "un revisado agota sus intentos con bloqueantes":
        low = review({**dict.fromkeys(CRITERIA, 4), "fidelidad-canon": 2})
        for _ in range(3):
            fake.script("writer", "revise", writer_script(chapter_call()))
            fake.script("editor", None, editor_script(low))
    elif cause == "un revisado agota sus intentos por una prohibida":
        banned = chapter_call(text=text_of(1249) + f" {BANNED}")
        fake.script("writer", "revise", writer_script(banned, banned, banned, chapter_call()))
    elif cause == "interrumpida con max_resumes agotado":
        with unit_of_work(session_factory) as uow:
            uow.session.get_one(Run, confirmed.run_id).resumes = production.config.max_resumes
        fake.script("writer", "revise", Script(steps=(Fail(result=True),)))
    else:
        script_revisions(fake, 3)
        script_judge(fake)
        if cause == "fallo de render":
            kit.pdf.outcomes.append(PdfOutcome(None, detail="Edge no arrancó"))

    assert await _worker(production, orchestrator).run_next() == confirmed.run_id

    run = run_of(session_factory, confirmed.run_id)
    assert (run.status, run.reason) == ("failed", FAILURES[cause])
    assert request_of(session_factory, confirmed.request_id).status == "rejected"
    base, candidate = versions(session_factory, v1.novel_id)
    assert (candidate.id, candidate.status, candidate.number) == (
        run.candidate_version_id,
        "discarded",
        None,
    )
    assert (base.status, base.number) == ("published", 1)
    assert version_fingerprint(session_factory, v1.v1_id) == before
    with session_factory() as session:
        current = current_version(session, v1.novel_id)
        assert current is not None
        assert current.id == v1.v1_id

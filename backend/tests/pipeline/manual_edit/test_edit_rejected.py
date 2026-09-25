"""019-C22 y 019-C23 · En el capítulo editado bloquean los validadores deterministas y el gate:
la ejecución termina `failed` con `edit_rejected`, sin reescribir nada, y la edición `rejected`."""

from __future__ import annotations

import dataclasses
import datetime as dt
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed, editor_script, review
from tests.pipeline.gate.conftest import (
    GateKit,
    LeanDouble,
    evaluation,
    gate_passes,
    judge_script,
)
from tests.pipeline.manual_edit.conftest import N
from tests.pipeline.manual_edit.test_edit_run import (
    edit_of,
    edited_review,
    queue_edit,
    renamed,
    rewritten_text,
    run_of,
)

from story_maker.agents.fake import FakeAgent
from story_maker.domain.banned_terms import normalize_token
from story_maker.formal.candidate import CandidateVerification
from story_maker.formal.result import INVARIANTS, ChronologyResult
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import Production
from story_maker.pipeline.report import build_report
from story_maker.pipeline.worker import Worker
from story_maker.store.models import (
    AuditLog,
    BannedTerm,
    Character,
    Event,
    EventCharacter,
    Place,
    Run,
    ValidatorResult,
    Version,
)


def _ban(session_factory: sessionmaker[Session], user_id: int, term: str) -> None:
    with session_factory() as session:
        session.add(
            BannedTerm(
                level="user",
                term=term,
                type="word",
                keywords=None,
                normalized=normalize_token(term),
                user_id=user_id,
            )
        )
        session.commit()


def _report(session_factory: sessionmaker[Session], run_id: int) -> dict[str, Any]:
    with session_factory() as session:
        return build_report(session, session.get_one(Run, run_id))


def assert_rejected_and_v1_current(
    session_factory: sessionmaker[Session], n: N, run_id: int, reason: str = "edit_rejected"
) -> Run:
    run = run_of(session_factory, run_id)
    assert (run.status, run.reason) == ("failed", reason), run.reason_detail
    assert edit_of(session_factory, run_id).status == "rejected"
    with session_factory() as session:
        if run.candidate_version_id is not None:
            assert session.get_one(Version, run.candidate_version_id).status == "discarded"
        published = session.query(Version).filter_by(novel_id=n.novel_id, status="published")
        assert [v.id for v in published] == [n.v1_id]
    return run


async def test_a_banned_term_added_before_the_run_starts_rejects_the_edit_without_any_role(
    n: N, fake: FakeAgent, worker: Worker, session_factory: sessionmaker[Session]
) -> None:
    run_id = queue_edit(session_factory, n, renamed(session_factory, n))
    _ban(session_factory, n.user_a, "Nala")

    await worker.run_next()

    assert_rejected_and_v1_current(session_factory, n, run_id)
    assert fake.sessions == []
    with session_factory() as session:
        denials = session.query(AuditLog).filter_by(
            origin="manual_edit", decision="deny", run_id=run_id
        )
        (deny,) = denials
        assert (deny.user_id, deny.novel_id) == (n.user_a, n.novel_id)
    unresolved = _report(session_factory, run_id)["unresolved"]
    assert any(
        d["chapter"] == 3 and d["validator"] == "palabras-prohibidas" and "Nala" in d["message"]
        for d in unresolved
    )


def candidate_id(
    session_factory: sessionmaker[Session], model: type[Any], base_id: int, n: N
) -> int:
    """El id que tendrá en la candidata la fila `base_id` de v1: la copia añade las filas de cada
    tabla en el orden de la base, tras el último id (SQLite)."""
    with session_factory() as session:
        last = max(row.id for row in session.query(model))
        rows = session.query(model).filter_by(version_id=n.v1_id).order_by(model.id)
        base = [r.id for r in rows]
    return last + 1 + base.index(base_id)


def dog_seen_in_chapter_7(session_factory: sessionmaker[Session], n: N, seed: Seed) -> None:
    """Un evento registrado del capítulo 7 de v1, en abril de 2026, con el perro presente."""
    with session_factory() as session:
        event = Event(
            version_id=n.v1_id,
            statement="el perro ladra en el faro",
            moment=dt.datetime(2026, 4, 2, 10),
            place_id=seed.places["Faro de Cabo Mayor"],
            type="ordinary",
            excluded_character_id=None,
            analepsis=False,
            origin="recorded",
            chapter=7,
            beat=1,
        )
        session.add(event)
        session.flush()
        session.add(EventCharacter(event_id=event.id, character_id=n.toby_id))
        session.commit()


def chapter_3_review(
    session_factory: sessionmaker[Session], n: N, seed: Seed, *, excludes_dog: bool = False
) -> dict[str, Any]:
    """La revisión del capítulo 3 editado con su evento de marzo de 2026: Marta y el perro en el
    faro o, si `excludes_dog`, un evento excluyente del perro."""
    dog = candidate_id(session_factory, Character, n.toby_id, n)
    marta = candidate_id(session_factory, Character, n.marta_id, n)
    place = candidate_id(session_factory, Place, seed.places["Faro de Cabo Mayor"], n)
    event: dict[str, Any] = {
        "statement": "el perro muere en el faro" if excludes_dog else "pasean por el faro",
        "moment": "2026-03-12T18:00:00",
        "place_id": place,
        "present": [{"character_id": marta}, {"character_id": dog}],
        "type": "exclusion" if excludes_dog else "ordinary",
        "excluded_character_id": dog if excludes_dog else None,
        "analepsis": False,
        "beat": 1,
    }
    return edited_review(session_factory, n, events=[event])


@dataclass
class T4Lean:
    """El doble de Lean del kit, que devuelve T4 violado con un testigo en el evento del capítulo
    3 y el del 7 de la candidata."""

    inner: LeanDouble

    async def __call__(self, run_id: int) -> CandidateVerification:
        with self.inner.session_factory() as session:
            candidate = session.get_one(Run, run_id).candidate_version_id
            events = session.query(Event).filter_by(version_id=candidate)
            by_chapter = {e.chapter: e.id for e in events if e.chapter in (3, 7)}
            dog = session.query(Character).filter_by(version_id=candidate, canonical_name="Toby")
            dog_id = dog.one().id
        self.inner.outcomes.append(
            ChronologyResult(
                "failed",
                {**dict.fromkeys(INVARIANTS, True), "T4": False},
                {"T4": (dog_id, by_chapter[3], by_chapter[7])},
            )
        )
        return await self.inner(run_id)


def worker_with_lean(production: Production, orchestrator: Orchestrator, kit: GateKit) -> Worker:
    gate = dataclasses.replace(kit.gate, lean=T4Lean(kit.lean))
    execute = dataclasses.replace(orchestrator, gate=gate).execute
    return Worker(
        production.session_factory,
        execute,
        max_resumes=production.config.max_resumes,
        clock=production.clock,
    )


def assert_rejected_by_the_gate(
    session_factory: sessionmaker[Session], n: N, run_id: int, fake: FakeAgent, validator: str
) -> None:
    assert_rejected_and_v1_current(session_factory, n, run_id)
    assert not any(s.request.role == "writer" for s in fake.sessions)
    assert gate_passes(session_factory, run_id) == [(1, "fail")]
    with session_factory() as session:
        (row,) = session.query(ValidatorResult).filter_by(
            run_id=run_id, chapter=None, validator=validator
        )
        attributed = [d for d in row.detail["defects"] if d["chapter"] == 3 and d["blocking"]]
    assert attributed
    detail = _report(session_factory, run_id)["reason_detail"]
    assert all(d["message"] in detail for d in attributed)


async def test_a_lean_witness_in_the_edited_chapter_rejects_the_edit_without_rewriting_chapter_7(
    n: N,
    seed: Seed,
    fake: FakeAgent,
    kit: GateKit,
    production: Production,
    orchestrator: Orchestrator,
    session_factory: sessionmaker[Session],
) -> None:
    dog_seen_in_chapter_7(session_factory, n, seed)
    run_id = queue_edit(session_factory, n, rewritten_text(session_factory, n))
    fake.script("editor", None, editor_script(chapter_3_review(session_factory, n, seed)))
    fake.script("judge", None, judge_script(evaluation(4)))

    await worker_with_lean(production, orchestrator, kit).run_next()

    assert_rejected_by_the_gate(session_factory, n, run_id, fake, "cronologia-lean")


async def test_a_judge_criterion_citing_the_edited_chapter_rejects_the_edit(
    n: N, fake: FakeAgent, worker: Worker, session_factory: sessionmaker[Session]
) -> None:
    run_id = queue_edit(session_factory, n, rewritten_text(session_factory, n))
    fake.script("editor", None, editor_script(edited_review(session_factory, n)))
    low = evaluation({"continuidad": 2}, chapters={"continuidad": [3]})
    fake.script("judge", None, judge_script(low))

    await worker.run_next()

    assert_rejected_by_the_gate(session_factory, n, run_id, fake, "juez-novela")


async def test_a_mandatory_element_the_edit_removed_rejects_the_edit(
    n: N, fake: FakeAgent, worker: Worker, session_factory: sessionmaker[Session]
) -> None:
    run_id = queue_edit(session_factory, n, rewritten_text(session_factory, n))
    fake.script("editor", None, editor_script(review()))
    fake.script("judge", None, judge_script(evaluation(4)))

    await worker.run_next()

    assert_rejected_by_the_gate(session_factory, n, run_id, fake, "elementos-obligatorios")

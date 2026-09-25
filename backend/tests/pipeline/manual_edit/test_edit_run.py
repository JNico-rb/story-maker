"""La ejecución `manual_edit` (019-C18 a 019-C28)."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.changes.conftest import version_fingerprint
from tests.pipeline.conftest import (
    CRITERIA,
    NOW,
    chapter_call,
    editor_script,
    review,
    writer_script,
)
from tests.pipeline.gate.conftest import GateKit, evaluation, judge_script
from tests.pipeline.manual_edit.conftest import N, chapter_text, clean_text

from story_maker.agents.fake import FakeAgent
from story_maker.lint.chapter import LINTERS
from story_maker.observability.null import NullObservability
from story_maker.pipeline.manual_edit.save import save_edit
from story_maker.pipeline.report import build_report
from story_maker.pipeline.worker import Worker
from story_maker.store.models import (
    Attempt,
    CanonCard,
    Chapter,
    Character,
    Fact,
    FactUsage,
    ManualEdit,
    Run,
    ValidatorResult,
    Version,
)

DETERMINISTIC = ("palabras-prohibidas", "longitud-capitulo", "nombres-exactos")


def queue_edit(
    session_factory: sessionmaker[Session], n: N, text: str, chapter: int = 3, base: int = 1
) -> int:
    outcome = save_edit(
        session_factory, novel_id=n.novel_id, chapter=chapter, text=text, base_version=base, now=NOW
    )
    assert isinstance(outcome, int), outcome
    return outcome


def candidate_fact(session_factory: sessionmaker[Session], base_fact_id: int, n: N) -> int:
    """El id que tendrá en la candidata el hecho `base_fact_id` de v1: la copia añade los hechos
    en el orden de la base, tras el último id (SQLite)."""
    with session_factory() as session:
        last = max(f.id for f in session.query(Fact))
        base = [f.id for f in session.query(Fact).filter_by(version_id=n.v1_id).order_by(Fact.id)]
    return last + 1 + base.index(base_fact_id)


def rewritten_text(session_factory: sessionmaker[Session], n: N) -> str:
    """El capítulo 3 con sus párrafos 2 y 3 reescritos: conserva todos los nombres."""
    paragraphs = chapter_text(session_factory, n.v1_id, 3).split("\n\n")
    fresh = clean_text(7, paragraphs=2).split("\n\n")
    return "\n\n".join([paragraphs[0], *fresh, *paragraphs[3:]])


def run_of(session_factory: sessionmaker[Session], run_id: int) -> Run:
    with session_factory() as session:
        return session.get_one(Run, run_id)


def edit_of(session_factory: sessionmaker[Session], run_id: int) -> ManualEdit:
    with session_factory() as session:
        return session.query(ManualEdit).filter_by(run_id=run_id).one()


def published(session_factory: sessionmaker[Session], n: N, number: int) -> Version:
    with session_factory() as session:
        return session.query(Version).filter_by(novel_id=n.novel_id, number=number).one()


def chapter_of(session_factory: sessionmaker[Session], version_id: int, number: int) -> Chapter:
    with session_factory() as session:
        return session.query(Chapter).filter_by(version_id=version_id, number=number).one()


def chapter_results(session_factory: sessionmaker[Session], run_id: int, chapter: int) -> list[str]:
    with session_factory() as session:
        rows = session.query(ValidatorResult).filter_by(run_id=run_id, chapter=chapter)
        return [r.validator for r in rows.order_by(ValidatorResult.id)]


def roles(fake: FakeAgent) -> list[tuple[str, int | None]]:
    return [(s.request.role, s.request.chapter) for s in fake.sessions]


def edited_review(session_factory: sessionmaker[Session], n: N, **extra: Any) -> dict[str, Any]:
    """Una revisión del capítulo 3 que conserva el uso del viaje a Cádiz."""
    return {**review(usages=[candidate_fact(session_factory, n.cadiz, n)]), **extra}


async def test_an_edit_without_changed_facts_publishes_the_chapter_as_saved(
    n: N,
    fake: FakeAgent,
    worker: Worker,
    kit: GateKit,
    telemetry: NullObservability,
    session_factory: sessionmaker[Session],
) -> None:
    text = rewritten_text(session_factory, n)
    v1_before = version_fingerprint(session_factory, n.v1_id)
    run_id = queue_edit(session_factory, n, text)
    fake.script("editor", None, editor_script(edited_review(session_factory, n)))
    fake.script("judge", None, judge_script(evaluation(4)))

    await worker.run_next()

    run = run_of(session_factory, run_id)
    assert run.status == "published", run.reason_detail
    v2 = published(session_factory, n, 2)
    assert v2.changed_chapters == [3]
    third = chapter_of(session_factory, v2.id, 3)
    assert third.text == text
    assert third.title == chapter_of(session_factory, n.v1_id, 3).title
    results = chapter_results(session_factory, run_id, 3)
    assert results == [*DETERMINISTIC, *LINTERS, "rubrica-capitulo"]
    scores = {s.name for s in telemetry.traces[f"run:{run_id}"].scores}
    assert {*DETERMINISTIC, *LINTERS, "rubrica-capitulo"} <= scores
    assert roles(fake) == [("editor", 3), ("judge", None)]
    assert kit.lean.calls == [run_id]
    assert edit_of(session_factory, run_id).status == "applied"
    assert version_fingerprint(session_factory, n.v1_id) == v1_before
    trace = telemetry.traces[f"run:{run_id}"]
    assert trace.name == "edicion-manual"
    (span,) = [s for s in trace.spans if s.name == "capitulo-3"]
    names = [c.name for c in span.children]
    assert names == [
        *(f"validador:{v}" for v in (*DETERMINISTIC, *LINTERS)),
        "rol:editor",
        "validador:rubrica-capitulo",
    ]
    inputs = json.loads(fake.sessions[0].request.message)["call_inputs"]
    assert inputs["text"] == text
    assert "dato" in inputs["manual_edit"]


def renamed(session_factory: sessionmaker[Session], n: N) -> str:
    return chapter_text(session_factory, n.v1_id, 3).replace("Toby", "Nala")


def rename_review(
    session_factory: sessionmaker[Session], n: N, value: str = "Nala"
) -> dict[str, Any]:
    name = candidate_fact(session_factory, n.toby_name, n)
    return edited_review(session_factory, n, changed_facts=[{"fact_id": name, "new_value": value}])


def script_revisions(fake: FakeAgent, count: int) -> None:
    for _ in range(count):
        fake.script("writer", "revise", writer_script(chapter_call(title="Revisado")))
        fake.script("editor", None, editor_script(review()))


def hashes(session_factory: sessionmaker[Session], version_id: int) -> dict[int, str]:
    with session_factory() as session:
        rows = session.query(Chapter).filter_by(version_id=version_id)
        return {c.number: c.content_hash for c in rows}


async def test_an_edit_that_changes_a_nominal_fact_propagates_to_the_affected_chapters(
    n: N, fake: FakeAgent, worker: Worker, kit: GateKit, session_factory: sessionmaker[Session]
) -> None:
    text = renamed(session_factory, n)
    run_id = queue_edit(session_factory, n, text)
    toby_name = candidate_fact(session_factory, n.toby_name, n)
    fake.script("editor", None, editor_script(rename_review(session_factory, n)))
    script_revisions(fake, 2)
    fake.script("judge", None, judge_script(evaluation(4)))

    await worker.run_next()

    run = run_of(session_factory, run_id)
    assert run.status == "published", run.reason_detail
    assert roles(fake) == [
        ("editor", 3),
        ("writer", 1),
        ("editor", 1),
        ("writer", 7),
        ("editor", 7),
        ("judge", None),
    ]
    writers = [s for s in fake.sessions if s.request.role == "writer"]
    for writer in writers:
        inputs = json.loads(writer.request.message)["call_inputs"]
        assert inputs["change"]["changed_facts"] == [
            {"subject": "Toby", "attribute": "name", "old_value": "Toby", "new_value": "Nala"}
        ]
        assert text not in writer.request.message
    v2 = published(session_factory, n, 2)
    assert v2.changed_chapters == [1, 3, 7]
    before, after = hashes(session_factory, n.v1_id), hashes(session_factory, v2.id)
    assert {c: after[c] for c in (2, 4, 5, 6, 8, 9, 10)} == {
        c: before[c] for c in (2, 4, 5, 6, 8, 9, 10)
    }
    assert chapter_of(session_factory, v2.id, 3).text == text
    with session_factory() as session:
        dog = session.get_one(Fact, toby_name)
        assert dog.value == "Nala"
        assert session.get_one(Character, dog.character_id).canonical_name == "Nala"
        usages = session.query(FactUsage).filter_by(fact_id=toby_name, chapter=3).count()
        assert usages == 1
        cards = session.query(CanonCard).filter_by(version_id=v2.id).all()
        assert any("Nala" in c.text for c in cards)
        assert not any("Toby" in c.text for c in cards)
        assert session.get_one(Character, n.toby_id).canonical_name == "Toby"
    assert kit.lean.calls == [run_id]


LOW = {**dict.fromkeys(CRITERIA, 4), "fidelidad-canon": 1}
BLOCKING = [{"criterion": "fidelidad-canon", "blocking": True, "message": "contradice el canon"}]


def attempts(session_factory: sessionmaker[Session], run_id: int, chapter: int) -> list[Any]:
    with session_factory() as session:
        rows = session.query(Attempt).filter_by(run_id=run_id, chapter=chapter)
        return [(a.number, a.outcome) for a in rows.order_by(Attempt.id)]


async def test_the_editor_scores_do_not_block_the_edited_chapter(
    n: N,
    fake: FakeAgent,
    worker: Worker,
    telemetry: NullObservability,
    session_factory: sessionmaker[Session],
) -> None:
    run_id = queue_edit(session_factory, n, renamed(session_factory, n))
    low_edited = {**rename_review(session_factory, n), **review(LOW, defects=BLOCKING)}
    low_edited["changed_facts"] = rename_review(session_factory, n)["changed_facts"]
    low_edited["fact_usages"] = rename_review(session_factory, n)["fact_usages"]
    fake.script("editor", None, editor_script(low_edited))
    script_revisions(fake, 1)
    fake.script("writer", "revise", writer_script(chapter_call(title="Revisado")))
    fake.script("editor", None, editor_script(review(LOW, defects=BLOCKING)))
    script_revisions(fake, 1)
    fake.script("judge", None, judge_script(evaluation(4)))

    await worker.run_next()

    assert run_of(session_factory, run_id).status == "published"
    assert not any(s.request.role == "writer" and s.request.chapter == 3 for s in fake.sessions)
    assert attempts(session_factory, run_id, 3) == [(1, "accept")]
    assert attempts(session_factory, run_id, 7) == [(1, "rewrite"), (2, "accept")]
    with session_factory() as session:
        rubric = (
            session.query(ValidatorResult)
            .filter_by(run_id=run_id, chapter=3, validator="rubrica-capitulo")
            .one()
        )
        assert rubric.passed is False
        assert any(d["blocking"] for d in rubric.detail["defects"])
        report = build_report(session, session.get_one(Run, run_id))
    assert any(
        d["chapter"] == 3 and d["validator"] == "rubrica-capitulo" and d["blocking"]
        for d in report["unresolved"]
    )
    scores = [s for s in telemetry.traces[f"run:{run_id}"].scores if s.name == "rubrica-capitulo"]
    assert scores[0].value == 0


async def test_a_gate_failure_attributed_only_to_another_chapter_rewrites_only_that_chapter(
    n: N, fake: FakeAgent, worker: Worker, session_factory: sessionmaker[Session]
) -> None:
    text = renamed(session_factory, n)
    run_id = queue_edit(session_factory, n, text)
    fake.script("editor", None, editor_script(rename_review(session_factory, n)))
    script_revisions(fake, 2)
    low = evaluation({"continuidad": 2}, chapters={"continuidad": [7]})
    fake.script("judge", None, judge_script(low))
    fake.script("writer", "rewrite", writer_script(chapter_call(title="Reescrito")))
    fake.script("editor", None, editor_script(review()))
    fake.script("judge", None, judge_script(evaluation(4)))

    await worker.run_next()

    run = run_of(session_factory, run_id)
    assert run.status == "published", run.reason_detail
    rewrites = [s.request.chapter for s in fake.sessions if s.request.mode == "rewrite"]
    assert rewrites == [7]
    assert not any(s.request.role == "writer" and s.request.chapter == 3 for s in fake.sessions)
    v2 = published(session_factory, n, 2)
    assert chapter_of(session_factory, v2.id, 3).text == text
    assert chapter_of(session_factory, v2.id, 7).title == "Reescrito"

"""Una pasada del gate: entrada, orden de las etapas, corte en la que no pasa, PDF, nombres
exactos sobre la novela y resultados con sus scores (012-C1, C2, C4, C7, C18, C24)."""

from __future__ import annotations

import asyncio
from typing import Any, cast

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    PhaseDouble,
    Seed,
    chapter_call,
    editor_script,
    review,
    writer_script,
)
from tests.pipeline.gate.conftest import (
    GateKit,
    evaluation,
    script_judges,
    script_rewrites,
    seed_chapters,
    seed_world,
    visual_defects,
)

from story_maker.agents.fake import FakeAgent
from story_maker.formal.result import ChronologyResult
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Trace
from story_maker.pipeline.gate.phase import PdfOutcome, VisualReviewOutcome
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import ChapterProducer, Production
from story_maker.pipeline.runs import RunStop
from story_maker.store.models import (
    Attempt,
    AuditLog,
    Chapter,
    Checkpoint,
    Run,
    ValidatorResult,
    Version,
)

STAGE_1 = {"elementos-obligatorios", "nombres-exactos", "palabras-prohibidas"}


def results(session_factory: sessionmaker[Session], run_id: int) -> list[ValidatorResult]:
    with session_factory() as session:
        return list(
            session.query(ValidatorResult)
            .filter(ValidatorResult.run_id == run_id, ValidatorResult.chapter.is_(None))
            .order_by(ValidatorResult.id)
            .all()
        )


def run_of(session_factory: sessionmaker[Session], run_id: int) -> Run:
    with session_factory() as session:
        run = session.get(Run, run_id)
        assert run is not None
        return run


def gate_passes(session_factory: sessionmaker[Session], run_id: int) -> list[tuple[int, str]]:
    with session_factory() as session:
        rows = session.query(Attempt).filter(
            Attempt.run_id == run_id, Attempt.evaluable == "gate_cycle"
        )
        return [(a.number, cast(str, a.outcome)) for a in rows.order_by(Attempt.number)]


# --- 012-C1 · Entrada al gate --------------------------------------------------------------


def test_accepting_chapter_10_moves_to_gate_and_opens_pass_1(
    session_factory: sessionmaker[Session],
    seed: Seed,
    fake: FakeAgent,
    production: Production,
    kit: GateKit,
    planning: PhaseDouble,
) -> None:
    with session_factory() as session:
        seed_world(session, seed.version_id)
        seed_chapters(session, seed.version_id)
        session.query(Chapter).filter(
            Chapter.version_id == seed.version_id, Chapter.number == 10
        ).delete()
        for k in range(1, 10):
            session.add(Checkpoint(run_id=seed.run_id, chapter=k, created_at=seed_now()))
        run = session.get(Run, seed.run_id)
        assert run is not None
        run.phase, run.chapter = "writing", 10
        session.commit()
    fake.script("writer", "write", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(review()))
    script_judges(fake, evaluation())

    orchestrator = Orchestrator(production=production, planning=planning, gate=kit.gate)
    asyncio.run(orchestrator.execute(seed.run_id))

    assert gate_passes(session_factory, seed.run_id) == [(1, "accept")]
    assert run_of(session_factory, seed.run_id).status == "published"


def test_accepting_chapter_9_stays_in_writing_and_runs_no_gate_validator(
    session_factory: sessionmaker[Session],
    seed: Seed,
    fake: FakeAgent,
    producer: ChapterProducer,
    trace: Trace,
    kit: GateKit,
) -> None:
    with session_factory() as session:
        for k in range(1, 9):
            session.add(Checkpoint(run_id=seed.run_id, chapter=k, created_at=seed_now()))
        run = session.get(Run, seed.run_id)
        assert run is not None
        run.phase, run.chapter = "writing", 9
        session.commit()
    fake.script("writer", "write", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(review()))

    asyncio.run(producer.produce_chapter(seed.run_id, 9, trace))

    run = run_of(session_factory, seed.run_id)
    assert (run.phase, run.chapter) == ("writing", 10)
    assert results(session_factory, seed.run_id) == []
    assert kit.lean.calls == [] and kit.pdf.calls == []


def test_the_gate_never_runs_on_a_candidate_without_its_10_chapters(
    session_factory: sessionmaker[Session], seed: Seed, kit: GateKit, trace: Trace
) -> None:
    with session_factory() as session:
        seed_world(session, seed.version_id)
        seed_chapters(session, seed.version_id)
        session.query(Chapter).filter(
            Chapter.version_id == seed.version_id, Chapter.number == 7
        ).delete()
        session.commit()

    with pytest.raises(RuntimeError, match="10 capítulos"):
        asyncio.run(kit.gate(seed.run_id, trace))

    assert results(session_factory, seed.run_id) == []


def seed_now() -> Any:
    from tests.pipeline.conftest import NOW

    return NOW


# --- 012-C2 · Una pasada limpia -----------------------------------------------------------------


def test_a_clean_pass_runs_the_four_stages_in_order_and_publishes(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    script_judges(fake, evaluation(4))
    with session_factory() as session:
        hashes = {c.number: c.content_hash for c in session.query(Chapter)}

    asyncio.run(kit.gate(at_gate.run_id, trace))

    names = [r.validator for r in results(session_factory, at_gate.run_id)]
    assert set(names[:3]) == STAGE_1 and len(names) == 6
    assert set(names[3:5]) == {"cronologia-lean", "juez-novela"}
    assert names[5] == "pdf-enlaces"
    assert kit.log.entries == ["cronologia-lean", "revision-visual", "pdf"]
    assert [s.request.role for s in fake.sessions] == ["judge"]
    assert gate_passes(session_factory, at_gate.run_id) == [(1, "accept")]
    with session_factory() as session:
        assert {c.number: c.content_hash for c in session.query(Chapter)} == hashes
        version = session.get(Version, at_gate.version_id)
        assert version is not None and version.status == "published"
    assert run_of(session_factory, at_gate.run_id).status == "published"


# --- 012-C4 · Un nombre no canónico en un capítulo --------------------------------------------


def test_a_non_canonical_name_in_a_chapter_is_attributed_to_that_chapter(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    with session_factory() as session:
        chapter = (
            session.query(Chapter)
            .filter(Chapter.version_id == at_gate.version_id, Chapter.number == 6)
            .one()
        )
        chapter.text = f"{chapter.text} Tobi ladró."
        session.commit()
    script_rewrites(fake, 1)
    script_judges(fake, evaluation())

    asyncio.run(kit.gate(at_gate.run_id, trace))

    first = results(session_factory, at_gate.run_id)[:3]
    exact = next(r for r in first if r.validator == "nombres-exactos")
    defects = cast(dict[str, Any], exact.detail)["defects"]
    assert not exact.passed
    assert [(d["chapter"], d["blocking"]) for d in defects] == [(6, True)]
    assert "Tobi" in defects[0]["message"] and "Toby" in defects[0]["message"]
    writers = [s for s in fake.sessions if s.request.role == "writer"]
    assert [(s.request.chapter, s.request.mode) for s in writers] == [(6, "rewrite")]


# --- 012-C7 · Una etapa que falla corta la pasada ------------------------------------------------


def test_a_failing_stage_1_skips_lean_judge_visual_review_and_pdf(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
    config: Any,
) -> None:
    with session_factory() as session:
        chapter = (
            session.query(Chapter)
            .filter(Chapter.version_id == at_gate.version_id, Chapter.number == 6)
            .one()
        )
        chapter.text = f"{chapter.text} Tobi ladró."
        session.commit()
    kit.visual.outcomes.append(VisualReviewOutcome())
    script_rewrites(fake, 1)
    script_judges(fake, evaluation())

    asyncio.run(kit.gate(at_gate.run_id, trace))

    by_pass = [cast(dict[str, Any], r.detail)["gate_cycle"] for r in results(session_factory, at_gate.run_id)]
    first_pass = [
        r.validator
        for r in results(session_factory, at_gate.run_id)
        if cast(dict[str, Any], r.detail)["gate_cycle"] == 1
    ]
    assert set(first_pass) == STAGE_1
    assert by_pass.count(1) == 3
    # la pasada 1 no llegó ni a Lean ni al juez: los de la tabla solo corren en la 2
    assert kit.lean.calls == [at_gate.run_id]
    assert kit.log.entries == ["cronologia-lean", "revision-visual", "pdf"]


def test_a_failing_stage_2_skips_visual_review_and_pdf(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    script_judges(fake, evaluation({"continuidad": 2}, {"continuidad": (4,)}), evaluation())
    script_rewrites(fake, 1)

    asyncio.run(kit.gate(at_gate.run_id, trace))

    assert kit.log.entries == ["cronologia-lean", "cronologia-lean", "revision-visual", "pdf"]
    assert gate_passes(session_factory, at_gate.run_id) == [(1, "rewrite"), (2, "accept")]


def test_a_failing_stage_3_skips_the_pdf(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    kit.visual.outcomes.append(visual_defects(3))
    script_judges(fake, evaluation(), evaluation())
    script_rewrites(fake, 1)

    asyncio.run(kit.gate(at_gate.run_id, trace))

    assert kit.log.entries == [
        "cronologia-lean",
        "revision-visual",
        "cronologia-lean",
        "revision-visual",
        "pdf",
    ]


def test_every_stage_1_validator_runs_even_if_the_first_fails_and_all_chapters_are_rewritten(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    with session_factory() as session:
        for number in (2, 6):
            chapter = (
                session.query(Chapter)
                .filter(Chapter.version_id == at_gate.version_id, Chapter.number == number)
                .one()
            )
            chapter.text = f"{chapter.text} Tobi ladró. Martha rió."
        session.commit()
    script_rewrites(fake, 2)
    script_judges(fake, evaluation())

    asyncio.run(kit.gate(at_gate.run_id, trace))

    first = [
        r for r in results(session_factory, at_gate.run_id)
        if cast(dict[str, Any], r.detail)["gate_cycle"] == 1
    ]
    assert {r.validator for r in first} == STAGE_1
    writers = [s.request.chapter for s in fake.sessions if s.request.role == "writer"]
    assert writers == [2, 6]


# --- 012-C18 · El PDF de la candidata ------------------------------------------------------


def test_a_generated_pdf_whose_links_resolve_publishes_with_its_path(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    script_judges(fake, evaluation())

    asyncio.run(kit.gate(at_gate.run_id, trace))

    with session_factory() as session:
        version = session.get(Version, at_gate.version_id)
        assert version is not None
        assert version.pdf_path == kit.pdf.path


def test_a_broken_internal_link_fails_with_render_failure_and_no_rewrite(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    kit.pdf.outcomes.append(PdfOutcome(kit.pdf.path, False, "cap-4 no resuelve"))
    script_judges(fake, evaluation())

    with pytest.raises(RunStop) as stop:
        asyncio.run(kit.gate(at_gate.run_id, trace))

    assert (stop.value.status, stop.value.reason) == ("failed", "render_failure")
    links = [r for r in results(session_factory, at_gate.run_id) if r.validator == "pdf-enlaces"]
    assert [(r.passed, r.score) for r in links] == [(False, 0.0)]
    assert not any(s.request.role == "writer" for s in fake.sessions)
    assert gate_passes(session_factory, at_gate.run_id) == [(1, "fail")]


def test_a_pdf_that_is_never_generated_fails_with_render_failure(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    kit.pdf.outcomes.append(PdfOutcome(None, detail="Edge no arrancó"))
    script_judges(fake, evaluation())

    with pytest.raises(RunStop) as stop:
        asyncio.run(kit.gate(at_gate.run_id, trace))

    assert (stop.value.status, stop.value.reason) == ("failed", "render_failure")
    assert not any(r.validator == "pdf-enlaces" for r in results(session_factory, at_gate.run_id))


# --- 012-C24 · Resultado y score de cada validador -------------------------------------------


def test_each_gate_validator_leaves_its_result_and_then_its_score_in_its_span(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
    telemetry: NullObservability,
) -> None:
    script_judges(fake, evaluation(4))

    asyncio.run(kit.gate(at_gate.run_id, trace))

    rows = results(session_factory, at_gate.run_id)
    assert {r.validator for r in rows} == {
        *STAGE_1,
        "cronologia-lean",
        "juez-novela",
        "pdf-enlaces",
    }
    assert all(r.version_id == at_gate.version_id and r.score == 1.0 for r in rows)
    scores = {s.name: s for s in trace.scores}
    for name in (*STAGE_1, "cronologia-lean", "juez-novela", "pdf-enlaces"):
        assert scores[name].value == 1
        assert scores[name].span is not None and scores[name].span.name == f"validador:{name}"
    for invariant in ("T1", "T2", "T3", "T4", "T5"):
        assert scores[f"cronologia-lean/{invariant}"].value == 1
    criteria = [n for n in scores if n.startswith("juez-novela/")]
    assert len(criteria) == 7
    assert scores["juez-novela/ritmo"].value == 4
    assert scores["juez-novela/ritmo"].comment == "justificación de ritmo"


def test_a_failing_pass_also_sends_its_scores_with_the_defect_chapters_in_the_detail(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    kit.lean.outcomes.append(
        ChronologyResult(
            "failed",
            {"T1": True, "T2": True, "T3": True, "T4": True, "T5": False},
            {"T5": (1, 999)},
        )
    )
    script_judges(fake, evaluation())

    with pytest.raises(Exception):  # noqa: B017, PT011 — el testigo no existe; basta el score
        asyncio.run(kit.gate(at_gate.run_id, trace))


def test_banned_terms_score_comment_names_term_level_and_variant(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    from story_maker.store.models import BannedTerm

    with session_factory() as session:
        session.add(
            BannedTerm(
                level="user",
                user_id=at_gate.user_id,
                term="tormenta",
                type="word",
                normalized="tormenta",
            )
        )
        chapter = (
            session.query(Chapter)
            .filter(Chapter.version_id == at_gate.version_id, Chapter.number == 4)
            .one()
        )
        chapter.text = f"{chapter.text} Hubo tormentas."
        session.commit()
    script_rewrites(fake, 1)
    # la reescritura sigue contando «tormentas»: la pasada 2 vuelve a fallar; la 3 agota
    fake.script("writer", "rewrite", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(review()))
    script_judges(fake, evaluation())

    asyncio.run(kit.gate(at_gate.run_id, trace))

    score = next(s for s in trace.scores if s.name == "palabras-prohibidas")
    assert score.value == 0
    assert score.comment is not None
    assert all(x in score.comment for x in ("tormenta", "user", "tormentas"))
    with session_factory() as session:
        decisions = (
            session.query(AuditLog)
            .filter(AuditLog.origin == "publication_gate")
            .order_by(AuditLog.id)
            .all()
        )
    assert [d.decision for d in decisions] == ["deny", "allow"]
    assert cast(list[dict[str, str]], decisions[0].detail)[0]["chapter"] == "4"

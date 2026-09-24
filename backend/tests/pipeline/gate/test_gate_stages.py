"""012-C7 · Una etapa que falla corta la pasada."""

from __future__ import annotations

import asyncio

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed, chapter_call, editor_script, review, writer_script
from tests.pipeline.gate.conftest import (
    STAGE_1,
    GateKit,
    append_to_chapter,
    evaluation,
    gate_passes,
    results_of_pass,
    script_judges,
    script_rewrites,
    seed_unused_element,
    visual_defects,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Trace
from story_maker.store.models import ChronologyFile


def _roles(fake: FakeAgent) -> list[str]:
    return [s.request.role for s in fake.sessions]


def test_a_failing_stage_1_skips_the_chronology_file_the_verifier_the_judge_stage_3_and_pdf(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    append_to_chapter(session_factory, at_gate.version_id, 6, "Tobi ladró.")
    script_rewrites(fake, 1)
    script_judges(fake, evaluation())

    asyncio.run(kit.gate(at_gate.run_id, trace))

    first = {r.validator for r in results_of_pass(session_factory, at_gate.run_id, 1)}
    assert first == STAGE_1
    # lo de la tabla solo corre en la pasada 2, tras la reescritura
    assert _roles(fake) == ["writer", "editor", "judge"]
    assert kit.lean.calls == [at_gate.run_id]
    assert kit.log.entries == ["cronologia-lean", "revision-visual", "pdf"]
    with session_factory() as session:
        assert session.query(ChronologyFile).count() == 1


def test_a_failing_stage_2_skips_stage_3_and_pdf(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    script_judges(fake, evaluation({"continuidad": 2}, {"continuidad": (4,)}), evaluation())
    script_rewrites(fake, 1)

    asyncio.run(kit.gate(at_gate.run_id, trace))

    first = {r.validator for r in results_of_pass(session_factory, at_gate.run_id, 1)}
    assert first == {*STAGE_1, "cronologia-lean", "juez-novela"}
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
    assert gate_passes(session_factory, at_gate.run_id) == [(1, "rewrite"), (2, "accept")]


def test_every_stage_1_validator_runs_even_if_the_first_fails_and_all_their_chapters_are_rewritten(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    fair = seed_unused_element(session_factory, at_gate, chapters=(2, 5))
    append_to_chapter(session_factory, at_gate.version_id, 6, "Tobi ladró.")
    fake.script("writer", "rewrite", writer_script(chapter_call(title="Reescrito")))
    fake.script("editor", None, editor_script(review(usages=[fair])))
    script_rewrites(fake, 2)
    script_judges(fake, evaluation())

    asyncio.run(kit.gate(at_gate.run_id, trace))

    first = results_of_pass(session_factory, at_gate.run_id, 1)
    assert {r.validator for r in first} == STAGE_1
    assert not any(r.passed for r in first if r.validator != "palabras-prohibidas")
    writers = [s.request.chapter for s in fake.sessions if s.request.role == "writer"]
    assert writers == [2, 5, 6]
    assert gate_passes(session_factory, at_gate.run_id) == [(1, "rewrite"), (2, "accept")]

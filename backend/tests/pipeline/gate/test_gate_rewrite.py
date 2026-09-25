"""012-C19 · La reescritura dirigida rehace solo los capítulos atribuidos y repite el gate.

Incluye lo que recibe el editor de un defecto Lean en la reescritura (012-C9, `architecture.md`
§9.4): la reescritura es donde viaja."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import FixedWindows, Seed
from tests.pipeline.gate.conftest import (
    STAGE_1,
    GateKit,
    chapter_hashes,
    evaluation,
    gate_passes,
    results_of_pass,
    run_of,
    script_judges,
    script_rewrites,
    seed_t1_witness_in_6,
)

from story_maker.agents.fake import FakeAgent
from story_maker.formal.result import INVARIANTS, ChronologyResult
from story_maker.observability.port import Trace
from story_maker.pipeline.windows import GATE_DEFECTS_NOTE, WriterWindow
from story_maker.store.models import Run


class PhaseSpyWindows(FixedWindows):
    """Las ventanas de la fixture, anotando la fase de la ejecución cuando el writer pide la
    suya."""

    def __init__(self) -> None:
        super().__init__()
        self.phases: list[tuple[int, str | None, int | None]] = []

    def writer(self, session: Session, version_id: int, chapter: int) -> WriterWindow:
        run = session.query(Run).filter(Run.candidate_version_id == version_id).one()
        self.phases.append((chapter, run.phase, run.chapter))
        return super().writer(session, version_id, chapter)


@pytest.fixture
def windows() -> PhaseSpyWindows:
    return PhaseSpyWindows()


def _call_inputs(message: str) -> dict[str, Any]:
    inputs: dict[str, Any] = json.loads(message)["call_inputs"]
    return inputs


def test_targeted_rewrite_redoes_only_the_attributed_chapters_in_order_and_repeats_the_gate(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
    windows: PhaseSpyWindows,
) -> None:
    first = evaluation({"continuidad": 2, "ritmo": 2}, {"continuidad": (5, 2), "ritmo": (5,)})
    script_judges(fake, first, evaluation())
    script_rewrites(fake, 2)
    before = chapter_hashes(session_factory, at_gate.version_id)

    asyncio.run(kit.gate(at_gate.run_id, trace))

    assert gate_passes(session_factory, at_gate.run_id) == [(1, "rewrite"), (2, "accept")]
    assert windows.phases == [(2, "rewriting", 2), (5, "rewriting", 5)]
    writers = [s.request for s in fake.sessions if s.request.role == "writer"]
    assert [(w.chapter, w.mode) for w in writers] == [(2, "rewrite"), (5, "rewrite")]
    received = {w.chapter: _call_inputs(w.message)["defects"] for w in writers}
    assert [(d["criterion"], d["blocking"]) for d in received[2]] == [("continuidad", True)]
    assert [(d["criterion"], d["blocking"]) for d in received[5]] == [
        ("continuidad", True),
        ("ritmo", False),
    ]
    after = chapter_hashes(session_factory, at_gate.version_id)
    assert {n for n in after if after[n] != before[n]} == {2, 5}
    assert {r.validator for r in results_of_pass(session_factory, at_gate.run_id, 2)} >= STAGE_1
    assert run_of(session_factory, at_gate.run_id).phase == "gate"
    for session in fake.sessions:
        if session.request.role in ("writer", "editor"):
            span = session.request.parent_span
            assert span is not None
            assert span.name == f"capitulo-{session.request.chapter}"


def test_a_lean_defect_reaches_the_writer_and_the_editor_with_its_precedence_over_beats(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    before, after = seed_t1_witness_in_6(session_factory, at_gate)
    holds = {t: t != "T1" for t in INVARIANTS}
    kit.lean.outcomes.append(ChronologyResult("failed", holds, {"T1": (before, after)}))
    script_judges(fake, evaluation(), evaluation())
    script_rewrites(fake, 1)

    asyncio.run(kit.gate(at_gate.run_id, trace))

    writer = next(s.request for s in fake.sessions if s.request.role == "writer")
    editor = next(s.request for s in fake.sessions if s.request.role == "editor")
    assert writer.chapter == 6
    [defect] = _call_inputs(writer.message)["defects"]
    assert defect["validator"] == "cronologia-lean"
    assert "T1" in defect["message"]
    gate_defects = _call_inputs(editor.message)["gate_defects"]
    assert gate_defects["note"] == GATE_DEFECTS_NOTE
    assert "cumple-beats" in gate_defects["note"]
    assert [d["message"] for d in gate_defects["defects"]] == [defect["message"]]
    assert gate_passes(session_factory, at_gate.run_id) == [(1, "rewrite"), (2, "accept")]

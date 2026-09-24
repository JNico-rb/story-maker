"""012-C18 · El PDF de la candidata es la última etapa."""

from __future__ import annotations

import asyncio

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed
from tests.pipeline.gate.conftest import (
    GateKit,
    evaluation,
    gate_passes,
    results,
    script_judges,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Trace
from story_maker.pipeline.gate.phase import PdfOutcome
from story_maker.pipeline.runs import RunStop
from story_maker.store.models import Version


def _no_writer(fake: FakeAgent) -> bool:
    return not any(s.request.role == "writer" for s in fake.sessions)


def test_a_generated_pdf_whose_links_resolve_publishes_with_its_path(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    script_judges(fake, evaluation())

    asyncio.run(kit.gate(at_gate.run_id, trace))

    assert kit.pdf.calls == [at_gate.version_id]
    with session_factory() as session:
        version = session.get(Version, at_gate.version_id)
        assert version is not None
        assert version.pdf_path == kit.pdf.path


def test_a_broken_internal_link_fails_with_render_failure_a_zero_score_and_no_rewrite(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    kit.pdf.outcomes.append(PdfOutcome(kit.pdf.path, links_passed=False, detail="cap-4 roto"))
    script_judges(fake, evaluation())

    with pytest.raises(RunStop) as stop:
        asyncio.run(kit.gate(at_gate.run_id, trace))

    assert (stop.value.status, stop.value.reason) == ("failed", "render_failure")
    links = [r for r in results(session_factory, at_gate.run_id) if r.validator == "pdf-enlaces"]
    assert [(r.passed, r.score) for r in links] == [(False, 0.0)]
    assert next(s for s in trace.scores if s.name == "pdf-enlaces").value == 0
    assert _no_writer(fake)
    assert gate_passes(session_factory, at_gate.run_id) == [(1, "fail")]


def test_a_pdf_that_is_never_generated_fails_with_render_failure_and_no_rewrite(
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
    assert _no_writer(fake)
    assert gate_passes(session_factory, at_gate.run_id) == [(1, "fail")]
    with session_factory() as session:
        version = session.get(Version, at_gate.version_id)
        assert version is not None
        assert version.status == "candidate"

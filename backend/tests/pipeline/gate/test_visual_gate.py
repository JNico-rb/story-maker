"""La etapa 3 real dentro del gate, con los dobles (017-C04, 017-C13 a 017-C18)."""

from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed
from tests.pipeline.gate.conftest import (
    GateKit,
    evaluation,
    gate_passes,
    run_of,
    script_judges,
)
from tests.pipeline.gate.visual import (
    EMPTY,
    faithful,
    job_of,
    make_settings,
    make_stage,
    reviewer_script,
    seed_visual,
    with_stage,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Trace
from story_maker.pipeline.production import Production


def test_a_matching_review_lets_the_gate_go_on_to_the_pdf_and_publish(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    kit: GateKit,
    trace: Trace,
    tmp_path: Path,
) -> None:
    seed_visual(session_factory, at_gate)
    script_judges(fake, evaluation(4))
    fake.script("visual_reviewer", None, reviewer_script(faithful()))
    gate = with_stage(kit, make_stage(production, make_settings(tmp_path)))

    asyncio.run(gate(at_gate.run_id, trace))

    assert kit.log.entries == ["cronologia-lean", "pdf"]
    assert gate_passes(session_factory, at_gate.run_id) == [(1, "accept")]
    assert run_of(session_factory, at_gate.run_id).status == "published"


def test_an_empty_view_makes_the_stage_deliver_a_render_failure(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    trace: Trace,
    tmp_path: Path,
) -> None:
    seed_visual(session_factory, at_gate)
    fake.script("visual_reviewer", None, reviewer_script(EMPTY))

    outcome = asyncio.run(make_stage(production, make_settings(tmp_path))(job_of(at_gate), trace))

    assert outcome.failure == "render_failure"
    assert outcome.reregister is False
    assert {d.criterion for d in outcome.defects} == {"portada", "indice", "capitulos", "ficha"}
    assert all(d.chapter is None for d in outcome.defects)
    for part in ("portada", "indice", "capitulos", "ficha"):
        assert part in outcome.detail

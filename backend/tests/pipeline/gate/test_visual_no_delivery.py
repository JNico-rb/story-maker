"""017-C14 · Una sesión sin entrega válida es un ciclo fallido, no un defecto de la novela."""

from __future__ import annotations

import asyncio
import dataclasses
from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import USAGE, Seed
from tests.pipeline.gate.conftest import (
    GateKit,
    chapter_hashes,
    evaluation,
    gate_passes,
    results,
    script_judges,
)
from tests.pipeline.gate.visual import (
    faithful,
    job_of,
    make_settings,
    make_stage,
    reviewer_script,
    seed_visual,
    with_stage,
)

from story_maker.agents.fake import Call, FakeAgent, Hang, Say, Script
from story_maker.config import Config
from story_maker.observability.port import Trace
from story_maker.pipeline.production import Production
from story_maker.pipeline.runs import RunStop
from story_maker.store.models import RoleSession


@pytest.fixture
def config(config: Config) -> Config:
    """Una sesión colgada agota su tiempo en un segundo."""
    return dataclasses.replace(config, session_timeout_seconds=1)


SNAPSHOTS = tuple(Call("browser_snapshot", {}) for _ in range(10))
NO_DELIVERY = {
    "turns_exhausted": Script(steps=(*SNAPSHOTS, Say("Fin.")), usage=USAGE),
    "time_exhausted": Script(steps=(Hang(),), usage=USAGE),
    "completed": Script(steps=(Say("No he visto nada."),), usage=USAGE),
}


@pytest.mark.parametrize("ending", list(NO_DELIVERY))
def test_a_reviewer_session_without_a_valid_delivery_is_no_comparison_result(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    trace: Trace,
    tmp_path: Path,
    ending: str,
) -> None:
    seed_visual(session_factory, at_gate)
    fake.script("visual_reviewer", None, NO_DELIVERY[ending])

    outcome = asyncio.run(make_stage(production, make_settings(tmp_path))(job_of(at_gate), trace))

    with session_factory() as session:
        [row] = session.query(RoleSession).filter(RoleSession.role == "visual_reviewer").all()
    assert row.outcome == ending
    assert outcome.no_valid_delivery is True
    assert (outcome.defects, outcome.failure, outcome.reregister) == ((), None, False)
    assert "revision-visual" not in [r.validator for r in results(session_factory, at_gate.run_id)]


def test_with_cycles_left_another_cycle_starts_without_rewriting_or_reregistering(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    kit: GateKit,
    trace: Trace,
    tmp_path: Path,
) -> None:
    seed_visual(session_factory, at_gate)
    hashes = chapter_hashes(session_factory, at_gate.version_id)
    script_judges(fake, evaluation(4), evaluation(4))
    fake.script("visual_reviewer", None, NO_DELIVERY["completed"])
    fake.script("visual_reviewer", None, reviewer_script(faithful()))
    gate = with_stage(kit, make_stage(production, make_settings(tmp_path)))

    asyncio.run(gate(at_gate.run_id, trace))

    assert gate_passes(session_factory, at_gate.run_id) == [(1, "rewrite"), (2, "accept")]
    assert {s.request.role for s in fake.sessions} == {"judge", "visual_reviewer"}
    assert chapter_hashes(session_factory, at_gate.version_id) == hashes
    assert kit.pdf.calls == [at_gate.version_id]


def test_with_the_cycles_exhausted_the_run_fails_with_retries_exhausted_and_never_a_pdf(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    kit: GateKit,
    trace: Trace,
    tmp_path: Path,
) -> None:
    seed_visual(session_factory, at_gate)
    script_judges(fake, *(evaluation(4) for _ in range(3)))
    for _ in range(3):
        fake.script("visual_reviewer", None, NO_DELIVERY["completed"])
    gate = with_stage(kit, make_stage(production, make_settings(tmp_path)))

    with pytest.raises(RunStop) as stop:
        asyncio.run(gate(at_gate.run_id, trace))

    assert (stop.value.status, stop.value.reason) == ("failed", "retries_exhausted")
    assert gate_passes(session_factory, at_gate.run_id) == [
        (1, "rewrite"),
        (2, "rewrite"),
        (3, "fail"),
    ]
    assert kit.pdf.calls == []
    assert {s.request.role for s in fake.sessions} == {"judge", "visual_reviewer"}

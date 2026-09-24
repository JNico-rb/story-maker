"""012-C2 · Una pasada limpia recorre las cuatro etapas en orden y publica."""

from __future__ import annotations

import asyncio

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed
from tests.pipeline.gate.conftest import (
    STAGE_1,
    GateKit,
    chapter_hashes,
    evaluation,
    gate_passes,
    results,
    run_of,
    script_judges,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Trace
from story_maker.store.models import Version


def test_a_clean_pass_runs_the_four_stages_in_order_once_each_and_publishes(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    script_judges(fake, evaluation(4))
    hashes = chapter_hashes(session_factory, at_gate.version_id)

    asyncio.run(kit.gate(at_gate.run_id, trace))

    names = [r.validator for r in results(session_factory, at_gate.run_id)]
    assert len(names) == 6
    assert set(names[:3]) == STAGE_1
    assert set(names[3:5]) == {"cronologia-lean", "juez-novela"}
    assert names[5] == "pdf-enlaces"
    assert kit.log.entries == ["cronologia-lean", "revision-visual", "pdf"]
    assert [s.request.role for s in fake.sessions] == ["judge"]
    assert gate_passes(session_factory, at_gate.run_id) == [(1, "accept")]
    assert chapter_hashes(session_factory, at_gate.version_id) == hashes
    with session_factory() as session:
        version = session.get(Version, at_gate.version_id)
        assert version is not None
        assert version.status == "published"
    assert run_of(session_factory, at_gate.run_id).status == "published"

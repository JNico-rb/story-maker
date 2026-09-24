"""012-C4 · Un nombre no canónico en un capítulo se atribuye a ese capítulo."""

from __future__ import annotations

import asyncio
from typing import Any, cast

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed
from tests.pipeline.gate.conftest import (
    GateKit,
    append_to_chapter,
    evaluation,
    gate_passes,
    results_of_pass,
    script_judges,
    script_rewrites,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Trace


def test_a_non_canonical_name_in_a_chapter_is_attributed_to_that_chapter_and_rewrites_it(
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

    exact = next(
        r
        for r in results_of_pass(session_factory, at_gate.run_id, 1)
        if r.validator == "nombres-exactos"
    )
    defects = cast(dict[str, Any], exact.detail)["defects"]
    assert not exact.passed
    assert [(d["chapter"], d["blocking"]) for d in defects] == [(6, True)]
    assert "Tobi" in defects[0]["message"]
    assert "Toby" in defects[0]["message"]
    writers = [s.request for s in fake.sessions if s.request.role == "writer"]
    assert [(w.chapter, w.mode) for w in writers] == [(6, "rewrite")]
    assert gate_passes(session_factory, at_gate.run_id) == [(1, "rewrite"), (2, "accept")]

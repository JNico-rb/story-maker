"""Integración de `revision-visual` en el gate con los dobles (017-C17, 017-C18)."""

from __future__ import annotations

import asyncio
import dataclasses
import json
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed, editor_script, review
from tests.pipeline.gate.conftest import (
    GateKit,
    chapter_hashes,
    evaluation,
    gate_passes,
    results,
    run_of,
    script_judges,
    with_gate_cycles,
)
from tests.pipeline.gate.visual import (
    ZAHARA,
    add_place,
    faithful,
    make_settings,
    make_stage,
    name_in_chapters,
    reviewer_script,
    seed_visual,
    with_stage,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Trace
from story_maker.pipeline.production import Production
from story_maker.pipeline.runs import RunStop


def event_in(place_id: int) -> dict[str, Any]:
    """Un evento narrado del capítulo 3 en ese lugar: re-registrar sustituye todos los del 3."""
    return {
        "statement": "algo ocurre allí al anochecer",
        "moment": "2031-05-02T20:00:00",
        "place_id": place_id,
        "present": [],
        "type": "ordinary",
        "analepsis": False,
        "beat": 2,
    }


def with_zahara() -> dict[str, Any]:
    delivery = faithful()
    delivery["ficha"].append({"name": ZAHARA, "links": [{"destination": "capitulo-3"}]})
    return delivery


def test_a_data_failure_goes_back_to_the_editor_without_writer_and_the_next_cycle_publishes(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    kit: GateKit,
    trace: Trace,
    tmp_path: Path,
) -> None:
    villaverde = seed_visual(session_factory, at_gate)
    zahara = add_place(session_factory, at_gate.version_id, ZAHARA)
    name_in_chapters(session_factory, at_gate, ZAHARA, (3,))
    hashes = chapter_hashes(session_factory, at_gate.version_id)
    script_judges(fake, evaluation(4), evaluation(4))
    fake.script(
        "editor",
        None,
        editor_script(
            review(
                usages=[at_gate.facts["marta"]],
                events=[event_in(villaverde), event_in(zahara)],
            )
        ),
    )
    fake.script("visual_reviewer", None, reviewer_script(with_zahara()))
    gate = with_stage(kit, make_stage(production, make_settings(tmp_path)))

    asyncio.run(gate(at_gate.run_id, trace))

    roles = [(s.request.role, s.request.chapter) for s in fake.sessions]
    assert ("editor", 3) in roles
    assert all(role != "writer" for role, _ in roles)
    [editor] = [s for s in fake.sessions if s.request.role == "editor"]
    inputs = json.loads(editor.request.message)["call_inputs"]
    [defect] = inputs["gate_defects"]["defects"]
    assert defect["validator"] == "revision-visual"
    assert f"«{ZAHARA}»" in defect["message"]
    assert chapter_hashes(session_factory, at_gate.version_id) == hashes
    assert gate_passes(session_factory, at_gate.run_id) == [(1, "rewrite"), (2, "accept")]
    visual = [
        r for r in results(session_factory, at_gate.run_id) if r.validator == "revision-visual"
    ]
    assert [r.passed for r in visual] == [False, True]
    assert kit.pdf.calls == [at_gate.version_id]
    assert run_of(session_factory, at_gate.run_id).status == "published"


def test_if_the_editor_never_registers_it_every_cycle_repeats_the_failure_until_retries_exhausted(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    kit: GateKit,
    trace: Trace,
    tmp_path: Path,
) -> None:
    villaverde = seed_visual(session_factory, at_gate)
    add_place(session_factory, at_gate.version_id, ZAHARA)
    name_in_chapters(session_factory, at_gate, ZAHARA, (3,))
    script_judges(fake, *(evaluation(4) for _ in range(3)))
    for _ in range(2):
        fake.script("editor", None, editor_script(review(events=[event_in(villaverde)])))
    gate = dataclasses.replace(
        with_gate_cycles(kit, 2), visual_review=make_stage(production, make_settings(tmp_path))
    )

    with pytest.raises(RunStop) as stop:
        asyncio.run(gate(at_gate.run_id, trace))

    assert (stop.value.status, stop.value.reason) == ("failed", "retries_exhausted")
    assert f"«{ZAHARA}»" in stop.value.detail
    assert gate_passes(session_factory, at_gate.run_id) == [
        (1, "rewrite"),
        (2, "rewrite"),
        (3, "fail"),
    ]
    assert [s.request.role for s in fake.sessions].count("editor") == 2
    assert all(s.request.role != "writer" for s in fake.sessions)
    visual = [
        r for r in results(session_factory, at_gate.run_id) if r.validator == "revision-visual"
    ]
    assert [r.passed for r in visual] == [False, False, False]
    assert kit.pdf.calls == []

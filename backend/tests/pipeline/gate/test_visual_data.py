"""La comprobación de datos de la ficha, antes de abrir el revisor (017-C10, 017-C11)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed
from tests.pipeline.gate.conftest import GateKit, evaluation, gate_passes, script_judges
from tests.pipeline.gate.visual import (
    ZAHARA,
    add_place,
    drop_usages,
    job_of,
    make_settings,
    make_stage,
    name_in_chapters,
    reviewer_sessions,
    seed_visual,
    with_stage,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Trace
from story_maker.pipeline.production import Production
from story_maker.pipeline.runs import RunStop


def test_an_entity_without_chapter_named_in_the_text_is_an_attributed_data_failure_no_reviewer(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    trace: Trace,
    tmp_path: Path,
) -> None:
    seed_visual(session_factory, at_gate)
    add_place(session_factory, at_gate.version_id, ZAHARA)
    name_in_chapters(session_factory, at_gate, ZAHARA, (3, 7))

    outcome = asyncio.run(make_stage(production, make_settings(tmp_path))(job_of(at_gate), trace))

    assert reviewer_sessions(fake) == []
    assert outcome.failure is None
    assert outcome.reregister is True
    assert [d.chapter for d in outcome.defects] == [3, 7]
    for defect in outcome.defects:
        assert (defect.validator, defect.criterion, defect.blocking) == (
            "revision-visual",
            "ficha",
            True,
        )
        assert f"«{ZAHARA}»" in defect.message
        assert "la ficha no" in defect.message


@pytest.mark.parametrize("with_zahara", [False, True], ids=["solo-toby", "toby-y-zahara"])
def test_an_entity_without_chapter_no_chapter_names_is_an_unattributable_defect(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    trace: Trace,
    tmp_path: Path,
    with_zahara: bool,
) -> None:
    seed_visual(session_factory, at_gate)
    drop_usages(session_factory, at_gate.facts["toby"])
    if with_zahara:
        add_place(session_factory, at_gate.version_id, ZAHARA)
        name_in_chapters(session_factory, at_gate, ZAHARA, (3,))

    outcome = asyncio.run(make_stage(production, make_settings(tmp_path))(job_of(at_gate), trace))

    assert reviewer_sessions(fake) == []
    assert outcome.failure == "unattributable_defect"
    [toby] = [d for d in outcome.defects if d.chapter is None]
    assert (toby.criterion, toby.blocking) == ("ficha", True)
    assert "«Toby»" in toby.message
    assert "«Toby»" in outcome.detail


def test_the_run_fails_with_unattributable_defect_naming_the_entity(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    kit: GateKit,
    trace: Trace,
    tmp_path: Path,
) -> None:
    seed_visual(session_factory, at_gate)
    drop_usages(session_factory, at_gate.facts["toby"])
    script_judges(fake, evaluation(4))
    gate = with_stage(kit, make_stage(production, make_settings(tmp_path)))

    with pytest.raises(RunStop) as stop:
        asyncio.run(gate(at_gate.run_id, trace))

    assert (stop.value.status, stop.value.reason) == ("failed", "unattributable_defect")
    assert "«Toby»" in stop.value.detail
    assert kit.pdf.calls == []
    assert gate_passes(session_factory, at_gate.run_id) == [(1, "fail")]

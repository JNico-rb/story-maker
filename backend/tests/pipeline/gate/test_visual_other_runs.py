"""017-C19 · La revisión visual corre en el gate de un cambio y de una edición manual."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed
from tests.pipeline.gate.conftest import seed_change_over_v3
from tests.pipeline.gate.visual import (
    faithful,
    make_settings,
    make_stage,
    name_fact,
    reviewer_script,
    reviewer_sessions,
    seed_visual,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Trace
from story_maker.pipeline.gate.phase import GateJob
from story_maker.pipeline.production import Production
from story_maker.store.models import Character, Run
from story_maker.store.session import unit_of_work
from story_maker.store.story_bible import change_fact_value


def _showing(name: str) -> dict[str, Any]:
    delivery = faithful()
    for entity in delivery["ficha"]:
        if entity["name"] == "Toby":
            entity["name"] = name
    return delivery


@pytest.mark.parametrize(
    ("run_type", "shown", "passes"),
    [
        ("change_request", "Toby", False),
        ("change_request", "Nala", True),
        ("manual_edit", "Toby", False),
        ("manual_edit", "Nala", True),
    ],
)
def test_the_visual_review_of_a_change_or_manual_edit_compares_with_its_own_candidate(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    trace: Trace,
    tmp_path: Path,
    run_type: str,
    shown: str,
    passes: bool,
) -> None:
    seed_visual(session_factory, at_gate)
    change = seed_change_over_v3(session_factory, at_gate)
    with unit_of_work(session_factory) as uow:
        toby = (
            uow.session.query(Character)
            .filter(Character.version_id == change.candidate_id, Character.canonical_name == "Toby")
            .one()
        )
        change_fact_value(uow, name_fact(uow.session, change.candidate_id, toby.id).id, "Nala")
        uow.session.get_one(Run, change.run_id).type = run_type
    fake.script("visual_reviewer", None, reviewer_script(_showing(shown)))
    job = GateJob(
        run_id=change.run_id,
        user_id=at_gate.user_id,
        novel_id=at_gate.novel_id,
        version_id=change.candidate_id,
        cycle=1,
        cycles_remaining=True,
    )
    stage = make_stage(production, make_settings(tmp_path))

    outcome = asyncio.run(stage(job, trace))

    [session] = reviewer_sessions(fake)
    assert f"/view/versions/{change.candidate_id}?" in session.request.message
    assert session.request.run_id == change.run_id
    if passes:
        assert (outcome.defects, outcome.failure) == ((), None)
    else:
        assert outcome.failure == "render_failure"
        assert {d.criterion for d in outcome.defects} == {"ficha"}
        assert any("«Nala»" in d.message for d in outcome.defects)

"""017-I3 · `revision-visual` no escribe canon ni capítulos: solo añade su resultado."""

from __future__ import annotations

import asyncio
import dataclasses
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import USAGE, Seed, editor_script, review
from tests.pipeline.gate.conftest import GateKit, evaluation, script_judges, with_gate_cycles
from tests.pipeline.gate.visual import (
    ZAHARA,
    add_place,
    faithful,
    job_of,
    make_settings,
    make_stage,
    name_in_chapters,
    reviewer_script,
    seed_visual,
)

from story_maker.agents.fake import Fail, FakeAgent, Say, Script
from story_maker.observability.port import Trace
from story_maker.pipeline.production import Production
from story_maker.pipeline.runs import RunStop
from story_maker.store.models import (
    CanonCard,
    Chapter,
    Character,
    Event,
    EventCharacter,
    Fact,
    FactUsage,
    OutlineChapter,
    Place,
    StyleSheet,
    ValidatorResult,
    Version,
    World,
)

VERSION_SCOPE = (
    Chapter,
    Character,
    Place,
    Fact,
    FactUsage,
    Event,
    EventCharacter,
    OutlineChapter,
    StyleSheet,
    World,
    CanonCard,
)


def fingerprint(session_factory: sessionmaker[Session]) -> dict[str, list[tuple[Any, ...]]]:
    """Cada fila de las tablas de ámbito versión, columna a columna."""
    with session_factory() as session:
        return {
            model.__tablename__: sorted(
                tuple(getattr(row, c.key) for c in inspect(model).column_attrs)
                for row in session.query(model)
            )
            for model in VERSION_SCOPE
        }


def _no_dedication() -> dict[str, Any]:
    delivery = faithful()
    delivery["portada"]["dedication"] = ""
    return delivery


@pytest.mark.parametrize("case", ["C04", "C06", "C10"])
def test_the_stage_leaves_story_bible_and_chapters_identical_and_only_adds_its_result(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    trace: Trace,
    tmp_path: Path,
    case: str,
) -> None:
    seed_visual(session_factory, at_gate)
    if case == "C10":
        add_place(session_factory, at_gate.version_id, ZAHARA)
        name_in_chapters(session_factory, at_gate, ZAHARA, (3, 7))
    else:
        delivery = faithful() if case == "C04" else _no_dedication()
        fake.script("visual_reviewer", None, reviewer_script(delivery))
    before = fingerprint(session_factory)
    with session_factory() as session:
        results_before = session.query(ValidatorResult).count()

    asyncio.run(make_stage(production, make_settings(tmp_path))(job_of(at_gate), trace))

    assert fingerprint(session_factory) == before
    with session_factory() as session:
        added = session.query(ValidatorResult).count() - results_before
        [row] = session.query(ValidatorResult).order_by(ValidatorResult.id.desc()).limit(1)
    assert added == 1
    assert row.validator == "revision-visual"


def _prepare(
    case: str, session_factory: sessionmaker[Session], seed: Seed, fake: FakeAgent
) -> None:
    if case == "datos":
        add_place(session_factory, seed.version_id, ZAHARA)
        name_in_chapters(session_factory, seed, ZAHARA, (3,))
        fake.script("editor", None, editor_script(review()))
    elif case == "render":
        fake.script("visual_reviewer", None, reviewer_script(_no_dedication()))
    elif case == "sin-entrega":
        fake.script("visual_reviewer", None, Script(steps=(Say("Nada."),), usage=USAGE))
    else:
        fake.script("visual_reviewer", None, Script(steps=(Fail(),), usage=USAGE))


@pytest.mark.parametrize("case", ["datos", "render", "sin-entrega", "sin-navegador"])
def test_a_cycle_where_the_visual_review_does_not_pass_generates_no_pdf_and_publishes_nothing(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    kit: GateKit,
    trace: Trace,
    tmp_path: Path,
    case: str,
) -> None:
    seed_visual(session_factory, at_gate)
    _prepare(case, session_factory, at_gate, fake)
    script_judges(fake, evaluation(4))
    gate = dataclasses.replace(
        with_gate_cycles(kit, 0), visual_review=make_stage(production, make_settings(tmp_path))
    )

    with pytest.raises(RunStop):
        asyncio.run(gate(at_gate.run_id, trace))

    assert kit.pdf.calls == []
    with session_factory() as session:
        assert session.get_one(Version, at_gate.version_id).status == "candidate"

"""017-I3 · `revision-visual` no escribe canon ni capítulos: solo añade su resultado."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed
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

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Trace
from story_maker.pipeline.production import Production
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

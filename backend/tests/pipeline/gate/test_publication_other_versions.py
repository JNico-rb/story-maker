"""012-I4 · Publicar no modifica ninguna otra versión (`VersionAnteriorConservada`)."""

from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed
from tests.pipeline.gate.conftest import (
    GateKit,
    evaluation,
    script_judges,
    seed_change_over_v3,
    version_of,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Trace
from story_maker.store.models import Base, Version
from story_maker.store.version_copy import VERSION_TABLES, rows_of_version


def _columns(row: Base) -> dict[str, Any]:
    return {attr.key: getattr(row, attr.key) for attr in inspect(type(row)).column_attrs}


def _version_rows(session_factory: sessionmaker[Session], version_id: int) -> dict[str, Any]:
    """Todas las filas de ámbito versión de `version_id`, y la de la versión misma."""
    with session_factory() as session:
        rows: dict[str, Any] = {
            model.__tablename__: [_columns(r) for r in rows_of_version(session, model, version_id)]
            for model in VERSION_TABLES
        }
        rows["versions"] = _columns(session.get_one(Version, version_id))
        return rows


def test_publishing_modifies_no_other_version(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    change = seed_change_over_v3(session_factory, at_gate)
    with session_factory() as session:
        others = [v.id for v in session.query(Version).filter(Version.id != change.candidate_id)]
    before = {v: _version_rows(session_factory, v) for v in others}
    assert before[change.base_id]["chapters"]
    script_judges(fake, evaluation())

    asyncio.run(kit.gate(change.run_id, trace))

    assert version_of(session_factory, change.candidate_id).status == "published"
    assert {v: _version_rows(session_factory, v) for v in others} == before

"""014-I2 · Receptor único: la petición literal no llega a ningún rol de la ejecución de cambio
ni a la candidata."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.changes.conftest import (
    V1,
    confirm,
    rename_toby,
    run_of,
    script_judge,
    script_revisions,
)
from tests.pipeline.gate.conftest import evaluation, script_rewrites

from story_maker.agents.fake import FakeAgent
from story_maker.pipeline.worker import Worker
from story_maker.store.models import Base

MARK = "marca-unica-7f3a"


def _candidate_rows(session_factory: sessionmaker[Session], version_id: int) -> list[str]:
    """Todo el contenido de ámbito versión de la candidata, fila a fila."""
    rows = []
    with session_factory() as session:
        for table in Base.metadata.sorted_tables:
            if "version_id" in table.c:
                query = select(table).where(table.c.version_id == version_id)
                rows += [repr(tuple(row)) for row in session.execute(query)]
    return rows


async def test_the_literal_request_reaches_no_role_of_the_change_run_nor_the_candidate(
    session_factory: sessionmaker[Session], v1: V1, fake: FakeAgent, worker: Worker
) -> None:
    confirmed = confirm(
        session_factory, v1.novel_id, v1.v1_id, rename_toby(v1), request=f"llámalo Nala {MARK}"
    )
    script_revisions(fake, 3)
    script_judge(fake, evaluation({"continuidad": 2}, {"continuidad": (4,)}), evaluation())
    script_rewrites(fake, 1)

    await worker.run_next()

    run = run_of(session_factory, confirmed.run_id)
    assert run.status == "published"
    roles = {s.request.role for s in fake.sessions}
    assert roles == {"writer", "editor", "judge"}
    inputs = [repr(s.request) + "".join(s.reads) for s in fake.sessions]
    assert not [i for i in inputs if MARK in i]
    candidate = _candidate_rows(session_factory, run.candidate_version_id or 0)
    assert candidate
    assert not [row for row in candidate if MARK in row]

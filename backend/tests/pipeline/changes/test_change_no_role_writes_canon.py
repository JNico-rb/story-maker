"""014-I3 · Ningún rol escribe canon: la huella de v1 tras 014-C13 (la de 014-C01 y 014-C10 está
en `tests/api/change_requests/test_i3_no_role_writes_canon.py`)."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker
from tests.api.change_requests.test_i3_no_role_writes_canon import v1_fingerprint
from tests.pipeline.changes.conftest import (
    V1,
    confirm,
    rename_toby,
    run_of,
    script_judge,
    script_revisions,
)

from story_maker.agents.fake import FakeAgent
from story_maker.pipeline.changes.run import start_change
from story_maker.pipeline.production import Production
from story_maker.pipeline.worker import Worker
from story_maker.store.models import Character, Fact


async def test_the_code_applies_the_change_only_to_the_candidate_and_v1_stays_as_it_was(
    session_factory: sessionmaker[Session],
    v1: V1,
    fake: FakeAgent,
    production: Production,
    worker: Worker,
) -> None:
    confirmed = confirm(session_factory, v1.novel_id, v1.v1_id, rename_toby(v1))
    before = v1_fingerprint(session_factory, v1.v1_id)
    assert before["facts"]

    start_change(production, confirmed.run_id)

    assert fake.sessions == []
    candidate_id = run_of(session_factory, confirmed.run_id).candidate_version_id
    with session_factory() as session:
        names = session.query(Fact.value).filter(
            Fact.version_id == candidate_id, Fact.attribute == "name"
        )
        assert "Nala" in {row[0] for row in names}
        dogs = session.query(Character.canonical_name).filter(Character.version_id == v1.v1_id)
        assert "Toby" in {row[0] for row in dogs}
    assert v1_fingerprint(session_factory, v1.v1_id) == before

    script_revisions(fake, 3)
    script_judge(fake)
    await worker.run_next()

    assert run_of(session_factory, confirmed.run_id).status == "published"
    assert v1_fingerprint(session_factory, v1.v1_id) == before

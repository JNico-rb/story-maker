"""014-C12 · Si al arrancar la versión vigente ya no es su base, la ejecución falla con
`stale_base`."""

from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.changes.conftest import (
    NOW,
    V1,
    change,
    confirm,
    rename_toby,
    request_of,
    run_of,
    script_judge,
    script_revisions,
    versions,
)

from story_maker.agents.fake import Call, FakeAgent, Script
from story_maker.observability.null import NullObservability
from story_maker.pipeline.changes.request import ProposalOut, request_change
from story_maker.pipeline.changes.selection import FactSelection
from story_maker.pipeline.production import Production
from story_maker.pipeline.worker import Worker
from story_maker.store.models import Fact


async def test_of_two_changes_over_v1_the_second_fails_with_stale_base_and_history_stays_linear(
    session_factory: sessionmaker[Session],
    v1: V1,
    fake: FakeAgent,
    worker: Worker,
    production: Production,
    telemetry: NullObservability,
) -> None:
    a = confirm(session_factory, v1.novel_id, v1.v1_id, rename_toby(v1))
    b = confirm(
        session_factory,
        v1.novel_id,
        v1.v1_id,
        change(v1.trait, "le da miedo el agua fría", "le encanta el agua fría"),
        created_at=NOW + dt.timedelta(minutes=1),
    )
    script_revisions(fake, 3)
    script_judge(fake)

    assert await worker.run_next() == a.run_id
    assert await worker.run_next() == b.run_id

    assert run_of(session_factory, a.run_id).status == "published"
    stale = run_of(session_factory, b.run_id)
    assert (stale.status, stale.reason) == ("failed", "stale_base")
    assert stale.candidate_version_id is None
    assert request_of(session_factory, a.request_id).status == "applied"
    assert request_of(session_factory, b.request_id).status == "rejected"
    rows = versions(session_factory, v1.novel_id)
    assert [(v.number, v.status) for v in rows] == [(1, "published"), (2, "published")]
    assert [v.base_version_id for v in rows] == [None, v1.v1_id]

    v2 = rows[1]
    with session_factory() as session:
        lighthouse = (
            session.query(Fact)
            .filter(Fact.version_id == v2.id, Fact.value == "Faro de Cabo Mayor")
            .one()
        )
    proposal = {"changes": [{"fact_id": lighthouse.id, "new_value": "Faro de Cabo Menor"}]}
    fake.script("planner", "change", Script(steps=(Call("propose_change", proposal),)))
    out = await request_change(
        agent_port=production.port,
        telemetry=telemetry,
        session_factory=session_factory,
        config=production.config,
        prompt="Eres el planner en modo cambio.",
        novel_id=v1.novel_id,
        user_id=v1.user_id,
        selection=FactSelection(type="fact", fact_id=lighthouse.id),
        request="el faro se llama Faro de Cabo Menor",
        now=NOW + dt.timedelta(hours=1),
    )
    assert isinstance(out, ProposalOut)
    assert out.proposal["changes"] == [
        {
            "fact_id": lighthouse.id,
            "old_value": "Faro de Cabo Mayor",
            "new_value": "Faro de Cabo Menor",
        }
    ]

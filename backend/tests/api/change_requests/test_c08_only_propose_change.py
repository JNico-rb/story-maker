"""014-C08 — El planner en modo cambio solo tiene `propose_change` (RT4)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, FakeAgent, Script
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Span
from story_maker.store import models

from .conftest import F, fact_selection, headers, rename

REQUEST = "el perro se llama Nala"


def _all_spans(spans: list[Span]) -> list[Span]:
    return [s for span in spans for s in (span, *_all_spans(span.children))]


def test_the_change_planner_only_has_propose_change_and_the_hook_denies_the_rest(
    client: TestClient,
    f: F,
    fake: FakeAgent,
    telemetry: NullObservability,
    session_factory: sessionmaker[Session],
) -> None:
    steps = (
        Call("submit_plan", {"chapters": []}),
        Call("Bash", {"command": "dir"}),
        Call("propose_change", rename(f.toby_name_fact, "Nala")),
    )
    fake.script("planner", "change", Script(steps=steps))

    response = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": REQUEST},
        headers=headers(f.user_a),
    )

    assert response.status_code == 201, response.text
    [session] = fake.sessions
    assert session.profile.whitelist == ("propose_change",)
    assert [spec.name for spec in session.request.tools] == ["propose_change"]
    assert session.reads[0].startswith("lista-blanca")
    assert session.reads[1].startswith("lista-blanca")
    with session_factory() as db:
        denials = (
            db.query(models.AuditLog)
            .filter_by(novel_id=f.novel_id, origin="policy_hook", decision="deny")
            .order_by(models.AuditLog.id)
            .all()
        )
        assert [(d.role, d.tool) for d in denials] == [
            ("planner", "submit_plan"),
            ("planner", "Bash"),
        ]
        attempts = db.query(models.Attempt).filter_by(change_request_id=response.json()["id"])
        assert [(a.number, a.outcome) for a in attempts] == [(1, "accept")]
    [trace] = [t for t in telemetry.traces.values() if t.name == "propuesta-de-cambio"]
    warnings = [
        (s.name, s.status_message or "")
        for s in _all_spans(trace.spans)
        if s.name.startswith("tool:") and s.level == "WARNING"
    ]
    assert [name for name, _ in warnings] == ["tool:submit_plan", "tool:Bash"]
    assert all(reason.startswith("lista-blanca") for _, reason in warnings)

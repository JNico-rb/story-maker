"""014-C04 — Una prohibida en la petición la deniega sin abrir el planner."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import FakeAgent
from story_maker.observability.null import NullObservability
from story_maker.store import models

from .conftest import F, fact_selection, headers, propose, rename

DENIED = {
    "global": ("que el perro se llame Zoquete", "zoquete", "global", "Zoquete"),
    "user del cliente A": ("que vayan al hospital", "hospital", "user", "hospital"),
    "novel con acento": ("que aparezca Márta", "marta", "novel", "Márta"),
}


def _ask(client: TestClient, f: F, request: str) -> tuple[int, object]:
    response = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": request},
        headers=headers(f.user_a),
    )
    return response.status_code, response.json()


@pytest.mark.parametrize("row", list(DENIED), ids=list(DENIED))
def test_a_banned_term_in_the_request_answers_422_with_term_level_and_variant(
    row: str, client: TestClient, f: F
) -> None:
    request, term, level, variant = DENIED[row]

    status, body = _ask(client, f, request)

    assert status == 422
    assert body == {
        "detail": {
            "reason": "palabras-prohibidas",
            "term": term,
            "level": level,
            "variant": variant,
        }
    }


@pytest.mark.parametrize("row", list(DENIED), ids=list(DENIED))
def test_a_denied_request_stays_rejected_and_logs_a_deny_located_in_the_request(
    row: str, client: TestClient, f: F, session_factory: sessionmaker[Session]
) -> None:
    request, term, level, variant = DENIED[row]

    _ask(client, f, request)

    with session_factory() as session:
        (change_request,) = session.query(models.ChangeRequest).all()
        assert change_request.status == "rejected"
        assert change_request.code_hash is None
        assert change_request.request == request
        (decision,) = session.query(models.AuditLog).filter_by(novel_id=f.novel_id).all()
        assert (decision.origin, decision.decision) == ("change_request", "deny")
        assert decision.detail == [
            {"term": term, "level": level, "variant": variant, "location": "request"}
        ]


@pytest.mark.parametrize("row", list(DENIED), ids=list(DENIED))
def test_a_denied_request_scores_zero_in_its_trace_and_opens_no_role_session(
    row: str,
    client: TestClient,
    f: F,
    session_factory: sessionmaker[Session],
    telemetry: NullObservability,
    fake: FakeAgent,
) -> None:
    request, term, level, variant = DENIED[row]

    _ask(client, f, request)

    (trace,) = telemetry.traces.values()
    assert trace.name == "propuesta-de-cambio"
    assert trace.session == str(f.novel_id)
    (score,) = [s for s in trace.scores if s.name == "palabras-prohibidas"]
    assert score.value == 0
    assert score.comment is not None
    for part in (term, level, variant):
        assert part in score.comment
    assert fake.sessions == []
    with session_factory() as session:
        assert session.query(models.RoleSession).count() == 0


def test_the_list_of_another_client_does_not_apply_and_the_request_goes_on(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    propose(fake, rename(f.toby_name_fact, "Nala"))

    status, body = _ask(client, f, "que vayan a la playa")

    assert status == 201, body
    with session_factory() as session:
        (change_request,) = session.query(models.ChangeRequest).all()
        assert change_request.status == "proposed"

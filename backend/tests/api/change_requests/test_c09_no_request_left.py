"""014-C09 — Sin proveedor, sin sitio en el techo o con la sesión agotada, no queda solicitud
(y 014-I11 en las respuestas 503: las decisiones ya tomadas se quedan en el audit log)."""

from __future__ import annotations

import asyncio
import dataclasses
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, Fail, FakeAgent, Hang, Say, Script, Step
from story_maker.config import Config
from story_maker.store import models

from .conftest import ClientBuilder, F, fact_selection, headers, propose, rename, with_planner_turns

REQUEST = "el perro se llama Nala"


def _post(client: TestClient, f: F) -> Any:
    return client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": REQUEST},
        headers=headers(f.user_a),
    )


def _script(fake: FakeAgent, *steps: Step) -> None:
    fake.script("planner", "change", Script(steps=steps))


def _assert_no_request(sf: sessionmaker[Session], f: F) -> None:
    with sf() as session:
        assert session.query(models.ChangeRequest).filter_by(novel_id=f.novel_id).count() == 0
        assert (
            session.query(models.Attempt).filter(models.Attempt.change_request_id.isnot(None))
        ).count() == 0


def _role_session_outcomes(sf: sessionmaker[Session], f: F) -> list[str]:
    with sf() as session:
        rows = session.query(models.RoleSession).filter_by(novel_id=f.novel_id)
        return [row.outcome for row in rows.order_by(models.RoleSession.id)]


def _change_request_decisions(sf: sessionmaker[Session], f: F) -> list[tuple[str, str]]:
    with sf() as session:
        rows = session.query(models.AuditLog).filter_by(
            novel_id=f.novel_id, origin="change_request"
        )
        return [(row.decision, row.detail[0]["location"]) for row in rows if row.detail]  # type: ignore[index]


def test_a_provider_failure_answers_503_and_leaves_no_request(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    _script(fake, Fail())

    response = _post(client, f)

    assert response.status_code == 503, response.text
    _assert_no_request(session_factory, f)
    assert _role_session_outcomes(session_factory, f) == ["infrastructure_failure"]


def test_a_provider_failure_after_an_invalid_attempt_answers_503_and_keeps_the_decisions(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    propose(fake, rename(f.toby_name_fact, "Zoquete"))
    _script(fake, Fail(result=True))

    response = _post(client, f)

    assert response.status_code == 503, response.text
    _assert_no_request(session_factory, f)
    assert _role_session_outcomes(session_factory, f) == ["completed", "infrastructure_failure"]
    assert ("deny", "tool_field") in _change_request_decisions(session_factory, f)

    propose(fake, rename(f.toby_name_fact, "Nala"))
    again = _post(client, f)

    assert again.status_code == 201, again.text


@pytest.mark.parametrize(
    ("tune", "steps", "outcome"),
    [
        (
            lambda config: with_planner_turns(config, 1),
            (Call("propose_change", {}), Call("propose_change", {"changes": []})),
            "turns_exhausted",
        ),
        (
            lambda config: dataclasses.replace(config, session_timeout_seconds=1),
            (Hang(result=True),),
            "time_exhausted",
        ),
    ],
    ids=["max-turns", "session-timeout"],
)
def test_a_session_exhausted_with_attempts_left_answers_503_and_leaves_no_request(
    build_client: ClientBuilder,
    config: Config,
    f: F,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    tune: Any,
    steps: tuple[Step, ...],
    outcome: str,
) -> None:
    client, _ceiling = build_client(tune(config))
    _script(fake, *steps)

    response = _post(client, f)

    assert response.status_code == 503, response.text
    _assert_no_request(session_factory, f)
    assert _role_session_outcomes(session_factory, f) == [outcome]


def test_a_session_that_ends_without_any_delivery_answers_503_and_leaves_no_request(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    _script(fake, Say("No sé qué proponer."))

    response = _post(client, f)

    assert response.status_code == 503, response.text
    _assert_no_request(session_factory, f)
    assert _role_session_outcomes(session_factory, f) == ["completed"]


def test_no_room_in_the_ceiling_within_the_wait_answers_503_without_opening_the_session(
    build_client: ClientBuilder,
    config: Config,
    f: F,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
) -> None:
    client, ceiling = build_client(dataclasses.replace(config, api_wait_seconds=1))
    propose(fake, rename(f.toby_name_fact, "Nala"))

    blocker = asyncio.new_event_loop()
    ticket = blocker.run_until_complete(ceiling.acquire(ceiling.limit, None))
    try:
        response = _post(client, f)
    finally:
        ceiling.release(ticket)
        blocker.close()

    assert response.status_code == 503, response.text
    _assert_no_request(session_factory, f)
    assert fake.sessions == []
    assert _role_session_outcomes(session_factory, f) == []


def test_a_reservation_that_never_fits_answers_422_without_opening_the_session(
    build_client: ClientBuilder,
    config: Config,
    f: F,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
) -> None:
    client, _ceiling = build_client(dataclasses.replace(config, token_ceiling=1))
    propose(fake, rename(f.toby_name_fact, "Nala"))

    response = _post(client, f)

    assert response.status_code == 422, response.text
    _assert_no_request(session_factory, f)
    assert fake.sessions == []
    assert _role_session_outcomes(session_factory, f) == []

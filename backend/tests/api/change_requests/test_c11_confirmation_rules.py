"""014-C11 — La confirmación exige el código vigente de una solicitud propia en estado
`proposed` (y 014-I4: sin un código válido no se encola nada)."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import FakeAgent
from story_maker.store import models
from story_maker.store.session import unit_of_work

from .conftest import F, MutableClock, fact_selection, headers, propose, rename

REQUEST = "el perro se llama Nala"


def _ask(client: TestClient, f: F, fake: FakeAgent) -> dict[str, Any]:
    propose(fake, rename(f.toby_name_fact, "Nala"))
    response = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": REQUEST},
        headers=headers(f.user_a),
    )
    assert response.status_code == 201, response.text
    return response.json()  # type: ignore[no-any-return]


def _confirm(client: TestClient, request_id: int, code: str, user_id: int) -> Any:
    return client.post(
        f"/api/change-requests/{request_id}/confirm",
        json={"code": code},
        headers=headers(user_id),
    )


def _state(sf: sessionmaker[Session], request_id: int) -> tuple[str, int | None]:
    with sf() as session:
        row = session.get_one(models.ChangeRequest, request_id)
        return row.status, row.run_id


def _runs(sf: sessionmaker[Session], f: F) -> int:
    with sf() as session:
        return session.query(models.Run).filter_by(novel_id=f.novel_id).count()


def test_a_wrong_code_or_another_requests_code_is_422_and_the_right_one_confirms_later(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    first = _ask(client, f, fake)
    second = _ask(client, f, fake)

    wrong = _confirm(client, first["id"], "no-es-el-codigo", f.user_a)
    others = _confirm(client, first["id"], second["code"], f.user_a)

    assert (wrong.status_code, others.status_code) == (422, 422)
    assert _state(session_factory, first["id"]) == ("proposed", None)
    assert _runs(session_factory, f) == 0
    assert _confirm(client, first["id"], first["code"], f.user_a).status_code == 202
    assert _state(session_factory, first["id"])[0] == "confirmed"


def test_the_right_code_at_14_min_59_s_confirms(
    client: TestClient,
    f: F,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    clock: MutableClock,
) -> None:
    body = _ask(client, f, fake)
    clock.advance(minutes=14, seconds=59)

    response = _confirm(client, body["id"], body["code"], f.user_a)

    assert response.status_code == 202, response.text
    assert _state(session_factory, body["id"]) == ("confirmed", response.json()["run_id"])


@pytest.mark.parametrize("minutes", [15, 16], ids=["15-min-exactos", "despues"])
def test_the_right_code_at_15_min_or_later_is_409_and_the_request_expires(
    client: TestClient,
    f: F,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    clock: MutableClock,
    minutes: int,
) -> None:
    body = _ask(client, f, fake)
    clock.advance(minutes=minutes)

    response = _confirm(client, body["id"], body["code"], f.user_a)

    assert response.status_code == 409, response.text
    assert _state(session_factory, body["id"]) == ("expired", None)
    assert _runs(session_factory, f) == 0


def test_the_same_code_twice_is_409_and_leaves_a_single_run(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    body = _ask(client, f, fake)
    first = _confirm(client, body["id"], body["code"], f.user_a)

    again = _confirm(client, body["id"], body["code"], f.user_a)

    assert (first.status_code, again.status_code) == (202, 409)
    assert _state(session_factory, body["id"]) == ("confirmed", first.json()["run_id"])
    assert _runs(session_factory, f) == 1


@pytest.mark.parametrize("status", ["rejected", "applied", "expired"])
def test_a_request_that_is_not_proposed_is_409_and_unchanged(
    client: TestClient,
    f: F,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    status: str,
) -> None:
    body = _ask(client, f, fake)
    with unit_of_work(session_factory) as uow:
        uow.session.get_one(models.ChangeRequest, body["id"]).status = status

    response = _confirm(client, body["id"], body["code"], f.user_a)

    assert response.status_code == 409, response.text
    assert _state(session_factory, body["id"]) == (status, None)
    assert _runs(session_factory, f) == 0


def test_another_clients_request_or_a_missing_one_is_404_and_unchanged(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    body = _ask(client, f, fake)

    foreign = _confirm(client, body["id"], body["code"], f.user_b)
    missing = _confirm(client, body["id"] + 1000, body["code"], f.user_a)

    assert (foreign.status_code, missing.status_code) == (404, 404)
    assert foreign.json() == missing.json()
    assert _state(session_factory, body["id"]) == ("proposed", None)
    assert _runs(session_factory, f) == 0

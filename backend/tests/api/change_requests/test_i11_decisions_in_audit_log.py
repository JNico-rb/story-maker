"""014-I11 — Toda decisión del motor sobre la petición y sobre los valores nuevos queda en el
audit log con origen `change_request`, también en las solicitudes rechazadas y en las
respuestas 503."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Fail, FakeAgent, Script
from story_maker.store import models

from .conftest import F, fact_selection, headers, propose, rename

REQUEST = "el perro se llama Nala"
BANNED_REQUEST = "el perro se llama zoquete"


def _banned_then_valid(fake: FakeAgent, f: F) -> None:
    propose(fake, rename(f.toby_name_fact, "Zoquete"), rename(f.toby_name_fact, "Nala"))


def _always_banned(fake: FakeAgent, f: F) -> None:
    propose(fake, *[rename(f.toby_name_fact, "Zoquete")] * 3)


def _banned_then_provider_failure(fake: FakeAgent, f: F) -> None:
    propose(fake, rename(f.toby_name_fact, "Zoquete"))
    fake.script("planner", "change", Script(steps=(Fail(result=True),)))


def _valid(fake: FakeAgent, f: F) -> None:
    propose(fake, rename(f.toby_name_fact, "Nala"))


def _nothing(fake: FakeAgent, f: F) -> None:
    pass


# (petición, guion del planner, respuesta, decisiones en orden: la petición y cada valor nuevo)
ROWS: dict[str, tuple[str, Callable[[FakeAgent, F], None], int, list[str]]] = {
    "aceptada": (REQUEST, _valid, 201, ["allow", "allow"]),
    "petición prohibida": (BANNED_REQUEST, _nothing, 422, ["deny"]),
    "valor prohibido y después válido": (
        REQUEST,
        _banned_then_valid,
        201,
        ["allow", "deny", "allow"],
    ),
    "rechazada al agotar los intentos": (
        REQUEST,
        _always_banned,
        422,
        ["allow", "deny", "deny", "deny"],
    ),
    "503 tras un valor prohibido": (REQUEST, _banned_then_provider_failure, 503, ["allow", "deny"]),
}


def _decisions(sf: sessionmaker[Session], f: F) -> list[tuple[str, int, str]]:
    with sf() as session:
        rows = (
            session.query(models.AuditLog)
            .filter_by(novel_id=f.novel_id, origin="change_request")
            .order_by(models.AuditLog.id)
        )
        return [(row.origin, row.user_id, row.decision) for row in rows]


@pytest.mark.parametrize(("request_text", "script", "status", "decisions"), ROWS.values(), ids=ROWS)
def test_every_engine_decision_on_the_request_and_the_new_values_is_logged_as_change_request(
    client: TestClient,
    f: F,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    request_text: str,
    script: Callable[[FakeAgent, F], None],
    status: int,
    decisions: list[str],
) -> None:
    script(fake, f)

    response: Any = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": request_text},
        headers=headers(f.user_a),
    )

    assert response.status_code == status, response.text
    assert _decisions(session_factory, f) == [
        ("change_request", f.user_a, decision) for decision in decisions
    ]

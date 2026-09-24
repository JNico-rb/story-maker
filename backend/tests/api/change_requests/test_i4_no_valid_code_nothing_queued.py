"""014-I4 — Sin un código válido no se encola nada. El código es de un solo uso, se guarda solo
como hash y caduca a los `confirmation_minutes` (el uso único y la caducidad, en 014-C11)."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import FakeAgent

from .conftest import F, fact_selection, headers, propose, rename

REQUEST = "el perro se llama Nala"


def _database_dump(sf: sessionmaker[Session]) -> str:
    """Todas las filas de todas las tablas, como texto."""
    with sf() as session:
        tables = session.execute(
            text("SELECT name FROM sqlite_master WHERE type = 'table'")
        ).scalars()
        rows: list[Any] = []
        for table in list(tables):
            # El nombre sale del catálogo de la propia base de datos, no de una entrada.
            rows.extend(session.execute(text(f'SELECT * FROM "{table}"')).all())  # noqa: S608
        return "\n".join(repr(tuple(row)) for row in rows)


def test_the_code_never_appears_in_plain_in_the_database_before_or_after_confirming(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    propose(fake, rename(f.toby_name_fact, "Nala"))
    body = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": REQUEST},
        headers=headers(f.user_a),
    ).json()
    assert "Nala" in _database_dump(session_factory)  # la búsqueda ve lo que guarda la solicitud
    assert body["code"] not in _database_dump(session_factory)

    confirmed = client.post(
        f"/api/change-requests/{body['id']}/confirm",
        json={"code": body["code"]},
        headers=headers(f.user_a),
    )

    assert confirmed.status_code == 202, confirmed.text
    assert body["code"] not in _database_dump(session_factory)

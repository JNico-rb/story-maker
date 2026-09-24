"""014-I3 — Ningún rol escribe canon: pedir y confirmar no cambian ninguna versión (huella del
contenido de v1 antes y después de 014-C01 y 014-C10; la de 014-C13, con la ejecución de
cambio)."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import FakeAgent
from story_maker.store import models

from .conftest import F, fact_selection, headers, propose, rename

REQUEST = "el perro se llama Nala"
# Filas de otras tablas que cuelgan de un hecho o de un evento de la versión, con su padre.
DEPENDENT = (
    (models.FactUsage, models.Fact, models.FactUsage.fact_id),
    (models.EventCharacter, models.Event, models.EventCharacter.event_id),
)


def _columns(row: Any) -> tuple[Any, ...]:
    return tuple(repr(getattr(row, c.key)) for c in row.__table__.columns)


def v1_fingerprint(sf: sessionmaker[Session], version_id: int) -> dict[str, list[tuple[Any, ...]]]:
    """Cada fila de la versión y de lo que cuelga de ella, columna a columna."""
    fingerprint: dict[str, list[tuple[Any, ...]]] = {}
    with sf() as session:
        fingerprint["versions"] = [_columns(session.get_one(models.Version, version_id))]
        for mapper in models.Base.registry.mappers:
            model = mapper.class_
            if "version_id" in model.__table__.columns:
                rows = session.query(model).filter_by(version_id=version_id).all()
                fingerprint[model.__tablename__] = sorted(_columns(r) for r in rows)
        for model, parent, parent_id in DEPENDENT:
            rows = session.query(model).join(parent, parent.id == parent_id)
            fingerprint[model.__tablename__] = sorted(
                _columns(r) for r in rows.filter(parent.version_id == version_id)
            )
    return fingerprint


def test_asking_and_confirming_leave_every_row_of_v1_as_it_was(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session]
) -> None:
    before = v1_fingerprint(session_factory, f.v1_id)
    assert before["chapters"]  # la huella ve el contenido de v1
    assert before["facts"]
    propose(fake, rename(f.toby_name_fact, "Nala"))

    body = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": REQUEST},
        headers=headers(f.user_a),
    ).json()
    after_asking = v1_fingerprint(session_factory, f.v1_id)
    confirmed = client.post(
        f"/api/change-requests/{body['id']}/confirm",
        json={"code": body["code"]},
        headers=headers(f.user_a),
    )

    assert confirmed.status_code == 202, confirmed.text
    assert after_asking == before
    assert v1_fingerprint(session_factory, f.v1_id) == before

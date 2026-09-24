"""Propiedad: lo ajeno responde como inexistente (002-C15 a 002-C21, I3).

Al cerrar la 002 todavía no hay rutas de recurso (spec, autorrevisión), así que estos casos se
ejercen con rutas de prueba, montadas solo aquí, una por tipo de identificador de §15.7 —
novela, ejecución, solicitud de cambio, entrada de nivel `user`, hecho extraído, entrada de nivel
`novel`, número de versión y de capítulo — usando el mismo mecanismo (`get_current_user_id`,
`owned_or_404`) que usará cada ruta real de las specs siguientes."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.api.app import create_app
from story_maker.api.dependencies import get_current_user_id
from story_maker.api.ownership import owned_or_404
from story_maker.store.models import Novel
from story_maker.store.session import create_schema, make_engine, make_session_factory

JWT_SECRET = "x" * 32
NOW = dt.datetime(2026, 1, 1)


@contextmanager
def _session(request: Request) -> Iterator[Session]:
    """Sesión de lectura para las rutas de prueba; evita `Depends(get_session)` como valor por
    defecto anidado (falso positivo de ruff B008 en cierres)."""
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def _mount_novel_route(app: FastAPI) -> FastAPI:
    @app.get("/api/_test/novels/{novel_id}")
    def get_novel(
        novel_id: int, request: Request, user_id: int = Depends(get_current_user_id)
    ) -> dict[str, int]:
        with _session(request) as session:
            novel = owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
            return {"id": novel.id}

    return app


@pytest.fixture
def session_factory(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = make_engine(tmp_path / "story-maker.db")
    create_schema(engine)
    yield make_session_factory(engine)
    engine.dispose()


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> TestClient:
    app = create_app(session_factory=session_factory, jwt_secret=JWT_SECRET)
    _mount_novel_route(app)
    return TestClient(app)


def _register_and_login(client: TestClient, email: str) -> tuple[int, str]:
    register = client.post("/api/auth/register", json={"email": email, "password": "contraseña-1"})
    login = client.post("/api/auth/login", json={"email": email, "password": "contraseña-1"})
    return register.json()["id"], login.json()["access_token"]


def _create_novel(session_factory: sessionmaker[Session], user_id: int) -> int:
    session = session_factory()
    try:
        novel = Novel(user_id=user_id, title=None, embedding_model="m", created_at=NOW)
        session.add(novel)
        session.commit()
        return novel.id
    finally:
        session.close()


class FakeClock:
    def __init__(self, now: dt.datetime) -> None:
        self._now = now

    def __call__(self) -> dt.datetime:
        return self._now

    def set(self, now: dt.datetime) -> None:
        self._now = now


def test_token_is_checked_before_ownership(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    a_id, _a_token = _register_and_login(client, "cliente-a@example.com")
    novel_id = _create_novel(session_factory, a_id)
    missing_id = novel_id + 999

    without_token_own_id = client.get(f"/api/_test/novels/{novel_id}")
    without_token_missing_id = client.get(f"/api/_test/novels/{missing_id}")

    assert without_token_own_id.status_code == 401
    assert without_token_missing_id.status_code == 401

    t0 = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.UTC)
    clock = FakeClock(t0)
    clocked_app = create_app(session_factory=session_factory, jwt_secret=JWT_SECRET, clock=clock)
    _mount_novel_route(clocked_app)
    clocked_client = TestClient(clocked_app)
    _, a_token = _register_and_login(clocked_client, "otro-a@example.com")
    clock.set(t0 + dt.timedelta(hours=25))  # tras access_token_hours (24h): caducado

    expired_own_id = clocked_client.get(
        f"/api/_test/novels/{novel_id}", headers={"Authorization": f"Bearer {a_token}"}
    )
    expired_missing_id = clocked_client.get(
        f"/api/_test/novels/{missing_id}", headers={"Authorization": f"Bearer {a_token}"}
    )

    assert expired_own_id.status_code == 401
    assert expired_missing_id.status_code == 401

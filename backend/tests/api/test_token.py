"""El `TokenDeAcceso` en las rutas protegidas (002-C11 a 002-C15, I2, I4).

Al cerrar la 002 todavía no hay rutas de recurso (§ Autorrevisión de la spec), así que estos
casos se ejercen con una ruta protegida de prueba, montada solo aquí, que expone la dependencia
`get_current_user_id` — el mismo mecanismo que usará cada ruta real de las specs siguientes."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.api.app import create_app
from story_maker.api.dependencies import get_current_user_id
from story_maker.store.session import create_schema, make_engine, make_session_factory

JWT_SECRET = "x" * 32


class FakeClock:
    def __init__(self, now: dt.datetime) -> None:
        self._now = now

    def __call__(self) -> dt.datetime:
        return self._now

    def set(self, now: dt.datetime) -> None:
        self._now = now


def _mount_whoami(app: FastAPI) -> FastAPI:
    @app.get("/api/_test/whoami")
    def whoami(user_id: int = Depends(get_current_user_id)) -> dict[str, int]:
        return {"user_id": user_id}

    return app


@pytest.fixture
def session_factory(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = make_engine(tmp_path / "story-maker.db")
    create_schema(engine)
    yield make_session_factory(engine)
    engine.dispose()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.UTC))


@pytest.fixture
def client(session_factory: sessionmaker[Session], clock: FakeClock) -> TestClient:
    app = create_app(session_factory=session_factory, jwt_secret=JWT_SECRET, clock=clock)
    _mount_whoami(app)
    return TestClient(app)


def _register_and_login(client: TestClient, email: str) -> tuple[int, str]:
    register = client.post("/api/auth/register", json={"email": email, "password": "contraseña-1"})
    login = client.post("/api/auth/login", json={"email": email, "password": "contraseña-1"})
    return register.json()["id"], login.json()["access_token"]


def test_a_valid_token_identifies_the_client(client: TestClient) -> None:
    a_id, a_token = _register_and_login(client, "cliente-a@example.com")
    b_id, b_token = _register_and_login(client, "cliente-b@example.com")

    as_a = client.get("/api/_test/whoami", headers={"Authorization": f"Bearer {a_token}"})
    as_b = client.get("/api/_test/whoami", headers={"Authorization": f"Bearer {b_token}"})

    assert as_a.status_code == 200
    assert as_a.json() == {"user_id": a_id}
    assert as_b.status_code == 200
    assert as_b.json() == {"user_id": b_id}


@pytest.mark.parametrize("scheme", ["Bearer", "bearer", "BEARER", "BeArEr"])
def test_the_bearer_scheme_is_accepted_in_any_case(client: TestClient, scheme: str) -> None:
    a_id, a_token = _register_and_login(client, "cliente-a@example.com")

    response = client.get("/api/_test/whoami", headers={"Authorization": f"{scheme} {a_token}"})

    assert response.status_code == 200
    assert response.json() == {"user_id": a_id}


def test_missing_or_malformed_token_answers_401(client: TestClient) -> None:
    _a_id, a_token = _register_and_login(client, "cliente-a@example.com")

    no_header = client.get("/api/_test/whoami")
    basic_scheme = client.get("/api/_test/whoami", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    bearer_without_token = client.get("/api/_test/whoami", headers={"Authorization": "Bearer"})
    token_in_query = client.get(f"/api/_test/whoami?token={a_token}")
    client.cookies.set("token", a_token)
    token_in_cookie = client.get("/api/_test/whoami")
    client.cookies.clear()
    not_a_jwt = client.get(
        "/api/_test/whoami", headers={"Authorization": "Bearer esto-no-es-un-jwt"}
    )

    responses = [
        no_header,
        basic_scheme,
        bearer_without_token,
        token_in_query,
        token_in_cookie,
        not_a_jwt,
    ]
    for response in responses:
        assert response.status_code == 401, response.text
        assert response.headers["WWW-Authenticate"] == "Bearer"
    bodies = {response.text for response in responses}
    assert len(bodies) == 1

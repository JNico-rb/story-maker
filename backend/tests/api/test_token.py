"""El `TokenDeAcceso` en las rutas protegidas (002-C11 a 002-C15, I2, I4).

Al cerrar la 002 todavía no hay rutas de recurso (§ Autorrevisión de la spec), así que estos
casos se ejercen con una ruta protegida de prueba, montada solo aquí, que expone la dependencia
`get_current_user_id` — el mismo mecanismo que usará cada ruta real de las specs siguientes."""

from __future__ import annotations

import datetime as dt
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import jwt
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


def _json(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


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


def test_a_tampered_or_misused_token_answers_401(client: TestClient, clock: FakeClock) -> None:
    a_id, a_token = _register_and_login(client, "cliente-a@example.com")
    b_id, _b_token = _register_and_login(client, "cliente-b@example.com")
    header_b64, payload_b64, sig_b64 = a_token.split(".")
    payload = jwt.decode(a_token, options={"verify_signature": False})

    last_char = sig_b64[-1]
    tampered_sig = sig_b64[:-1] + ("A" if last_char != "A" else "B")
    changed_signature = f"{header_b64}.{payload_b64}.{tampered_sig}"

    sub_payload = dict(payload, sub=str(b_id))
    changed_sub = (
        f"{header_b64}.{jwt.utils.base64url_encode(_json(sub_payload)).decode()}.{sig_b64}"
    )

    other_secret = jwt.encode(payload, "y" * 32, algorithm="HS256")
    alg_none = jwt.encode(payload, key=None, algorithm="none")
    other_algorithm = jwt.encode(payload, JWT_SECRET, algorithm="HS512")
    no_exp = jwt.encode(
        {k: v for k, v in payload.items() if k != "exp"}, JWT_SECRET, algorithm="HS256"
    )
    view_token_audience = jwt.encode(dict(payload, aud="view_token"), JWT_SECRET, algorithm="HS256")
    other_issuer = jwt.encode(dict(payload, iss="otro"), JWT_SECRET, algorithm="HS256")
    no_sub = jwt.encode(
        {k: v for k, v in payload.items() if k != "sub"}, JWT_SECRET, algorithm="HS256"
    )
    unknown_sub = jwt.encode(dict(payload, sub="999999"), JWT_SECRET, algorithm="HS256")

    tokens = [
        changed_signature,
        changed_sub,
        other_secret,
        alg_none,
        other_algorithm,
        no_exp,
        view_token_audience,
        other_issuer,
        no_sub,
        unknown_sub,
    ]
    for token in tokens:
        response = client.get("/api/_test/whoami", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401, (token, response.text)

    still_a = client.get("/api/_test/whoami", headers={"Authorization": f"Bearer {a_token}"})
    assert still_a.status_code == 200
    assert still_a.json() == {"user_id": a_id}

"""Registro y acceso (002-C01 a 002-C10)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.api.app import create_app
from story_maker.store.models import User
from story_maker.store.session import create_schema, make_engine, make_session_factory

JWT_SECRET = "x" * 32


@pytest.fixture
def session_factory(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = make_engine(tmp_path / "story-maker.db")
    create_schema(engine)
    yield make_session_factory(engine)
    engine.dispose()


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> TestClient:
    app = create_app(session_factory=session_factory, jwt_secret=JWT_SECRET)
    return TestClient(app)


def _users(session_factory: sessionmaker[Session]) -> list[User]:
    session = session_factory()
    try:
        return list(session.query(User).all())
    finally:
        session.close()


def test_valid_registration_creates_a_bcrypt_hashed_user(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": "cliente-a@example.com", "password": "contraseña-1"},
    )

    assert response.status_code == 201
    assert set(response.json()) == {"id", "email"}
    assert response.json()["email"] == "cliente-a@example.com"

    (user,) = _users(session_factory)
    assert user.created_at is not None
    assert user.password_hash != "contraseña-1"
    assert bcrypt.checkpw("contraseña-1".encode(), user.password_hash.encode("utf-8"))


def test_the_email_is_stored_normalized(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": "  Cliente-A@Example.COM ", "password": "contraseña-1"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "cliente-a@example.com"

    (user,) = _users(session_factory)
    assert user.email == "cliente-a@example.com"

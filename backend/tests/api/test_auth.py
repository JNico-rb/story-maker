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


def test_an_already_registered_email_does_not_create_another_account(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    client.post(
        "/api/auth/register",
        json={"email": "cliente-a@example.com", "password": "contraseña-1"},
    )

    response = client.post(
        "/api/auth/register",
        json={"email": "CLIENTE-A@example.com", "password": "otra-contraseña"},
    )

    assert response.status_code == 409
    assert len(_users(session_factory)) == 1

    original_login = client.post(
        "/api/auth/login",
        json={"email": "cliente-a@example.com", "password": "contraseña-1"},
    )
    assert original_login.status_code == 200

    new_login = client.post(
        "/api/auth/login",
        json={"email": "cliente-a@example.com", "password": "otra-contraseña"},
    )
    assert new_login.status_code == 401


@pytest.mark.parametrize(
    "email",
    [
        "cliente-a.example.com",  # sin arroba
        "cliente-a@@example.com",  # dos arrobas
        "@example.com",  # parte local vacía
        "cliente-a@example",  # dominio sin punto
        "cliente a@example.com",  # espacio interior
    ],
)
def test_an_email_without_email_shape_is_rejected(
    client: TestClient, session_factory: sessionmaker[Session], email: str
) -> None:
    response = client.post("/api/auth/register", json={"email": email, "password": "contraseña-1"})

    assert response.status_code == 422
    assert _users(session_factory) == []


@pytest.mark.parametrize(
    "email",
    [
        "cliente-a@.example.com",
        "cliente-a@example.com.",
    ],
)
def test_a_domain_starting_or_ending_with_a_dot_is_rejected(
    client: TestClient, session_factory: sessionmaker[Session], email: str
) -> None:
    response = client.post("/api/auth/register", json={"email": email, "password": "contraseña-1"})

    assert response.status_code == 422
    assert _users(session_factory) == []


@pytest.mark.parametrize(
    ("password", "expected_status"),
    [
        ("a" * 7, 422),
        ("a" * 8, 201),
        ("a" * 72, 201),
        ("a" * 73, 422),
        ("€" * 24, 201),  # 24 caracteres, 72 bytes UTF-8
        ("€" * 25, 422),  # 75 bytes UTF-8
    ],
)
def test_password_limits(
    client: TestClient,
    session_factory: sessionmaker[Session],
    password: str,
    expected_status: int,
) -> None:
    response = client.post(
        "/api/auth/register", json={"email": "cliente-a@example.com", "password": password}
    )

    assert response.status_code == expected_status
    if expected_status == 422:
        assert _users(session_factory) == []
        assert password not in response.text


def test_a_254_character_well_formed_email_is_accepted(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    email = "a" * 242 + "@example.com"
    assert len(email) == 254

    response = client.post("/api/auth/register", json={"email": email, "password": "contraseña-1"})

    assert response.status_code == 201


def test_a_255_character_well_formed_email_is_rejected(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    email = "a" * 243 + "@example.com"
    assert len(email) == 255

    response = client.post("/api/auth/register", json={"email": email, "password": "contraseña-1"})

    assert response.status_code == 422
    assert _users(session_factory) == []


@pytest.mark.parametrize(
    "body",
    [
        {"password": "contraseña-1"},
        {"email": "cliente-a@example.com"},
        {"email": 12345678, "password": "contraseña-1"},
        {"email": "cliente-a@example.com", "password": True},
    ],
)
def test_registration_with_an_incomplete_body_is_rejected(
    client: TestClient, session_factory: sessionmaker[Session], body: dict[str, object]
) -> None:
    response = client.post("/api/auth/register", json=body)

    assert response.status_code == 422
    assert _users(session_factory) == []

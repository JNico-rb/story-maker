"""Invariantes de toda la API: token obligatorio salvo registro y acceso, identidad solo del
token (002-I2, 002-I4)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.api.app import create_app
from story_maker.store.session import create_schema, make_engine, make_session_factory

JWT_SECRET = "x" * 32
PUBLIC_ROUTES = {("/api/auth/register", "POST"), ("/api/auth/login", "POST")}
# Crece con cada spec de rutas: una ruta nueva sin su fila aquí hace fallar la prueba.
PROTECTED_ROUTES = {
    ("/api/novels/{novel_id}/story-bible", "GET"),  # 009
    ("/api/novels/{novel_id}/versions", "GET"),  # 013
    ("/api/novels/{novel_id}/versions/{number}", "GET"),  # 013
    ("/api/novels/{novel_id}/versions/{number}/pdf", "GET"),  # 013
}


@pytest.fixture
def session_factory(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = make_engine(tmp_path / "story-maker.db")
    create_schema(engine)
    yield make_session_factory(engine)
    engine.dispose()


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> TestClient:
    return TestClient(create_app(session_factory=session_factory, jwt_secret=JWT_SECRET))


def _api_routes(client: TestClient) -> set[tuple[str, str]]:
    """Lee las rutas y métodos de `/api` del esquema OpenAPI: en esta versión de FastAPI,
    `app.routes` no expone las de un router incluido con `include_router` (envuelve en
    `_IncludedRouter`), pero el esquema sí las resuelve todas."""
    schema = client.app.openapi()
    return {
        (path, method.upper())
        for path, methods in schema["paths"].items()
        if path.startswith("/api")
        for method in methods
    }


def test_every_api_route_requires_a_token_except_register_and_login(client: TestClient) -> None:
    """Recorre todas las rutas de `/api` que tiene la aplicación (las que haya en cada momento):
    sin token, cada una que no sea el registro o el acceso responde 401; la lista de rutas
    públicas tiene exactamente esas dos (002-I2)."""
    routes = _api_routes(client)

    assert routes == PUBLIC_ROUTES | PROTECTED_ROUTES

    for path, method in routes - PUBLIC_ROUTES:
        response = client.request(method, path)
        assert response.status_code == 401, (path, method)


def test_no_openapi_schema_declares_a_client_or_owner_field(client: TestClient) -> None:
    """Ninguna entrada del esquema OpenAPI declara un campo de cliente o propietario: el cliente
    de una petición sale solo del token (002-I4, además de 002-C21)."""
    schema = client.app.openapi()
    suspicious_names = {"user_id", "client_id", "owner_id", "cliente_id", "usuario_id"}

    offenders = [
        (schema_name, prop_name)
        for schema_name, definition in schema.get("components", {}).get("schemas", {}).items()
        for prop_name in definition.get("properties", {})
        if prop_name in suspicious_names
    ]

    assert offenders == []

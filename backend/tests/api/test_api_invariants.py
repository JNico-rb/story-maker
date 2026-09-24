"""Invariantes de toda la API: token obligatorio salvo registro y acceso, identidad solo del
token (002-I2, 002-I4)."""

from __future__ import annotations

from fastapi.testclient import TestClient

PUBLIC_ROUTES = {("/api/auth/register", "POST"), ("/api/auth/login", "POST")}
# Crece con cada spec de rutas: una ruta nueva sin su fila aquí hace fallar la prueba.
PROTECTED_ROUTES = {
    ("/api/novels/{novel_id}/runs", "POST"),  # 011
    ("/api/runs/{run_id}", "GET"),  # 011
    ("/api/novels/{novel_id}/story-bible", "GET"),  # 009
    ("/api/novels/{novel_id}/versions", "GET"),  # 013
    ("/api/novels/{novel_id}/versions/{number}", "GET"),  # 013
    ("/api/novels/{novel_id}/versions/{number}/pdf", "GET"),  # 013
}

# Toda ruta nueva de /api entra aquí (002-I2, 002-I3): así la ruta de una spec nueva, si no
# exige token, falla esta prueba hasta que se sume a `PUBLIC_ROUTES` a propósito.
NOVEL_ROUTES = {
    ("/api/novels", "POST"),
    ("/api/novels", "GET"),
    ("/api/novels/{novel_id}", "GET"),
    ("/api/novels/{novel_id}/interview/messages", "GET"),
    ("/api/novels/{novel_id}/interview/messages", "POST"),
    ("/api/novels/{novel_id}/brief", "GET"),
    ("/api/novels/{novel_id}/brief/confirm", "POST"),
    ("/api/novels/{novel_id}/brief/extracted-facts/{fact_id}", "PATCH"),
    ("/api/banned-terms", "GET"),
    ("/api/banned-terms", "POST"),
    ("/api/banned-terms/{term_id}", "DELETE"),
    ("/api/novels/{novel_id}/free-texts", "POST"),
    ("/api/novels/{novel_id}/banned-terms", "GET"),
    ("/api/novels/{novel_id}/banned-terms", "POST"),
    ("/api/novels/{novel_id}/banned-terms/{term_id}", "DELETE"),
    ("/api/novels/{novel_id}/audit-log", "GET"),
}
ALL_ROUTES = PUBLIC_ROUTES | PROTECTED_ROUTES | NOVEL_ROUTES

# `client` (con `agent_port`, `telemetry`, `config` y `workspace` ya montados) sale de
# `tests/api/conftest.py`, compartido con el resto de las pruebas de la API de 008.


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

    assert routes == ALL_ROUTES  # crece con cada spec de rutas (008-C01 en adelante)

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

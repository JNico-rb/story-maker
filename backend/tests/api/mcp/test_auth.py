"""015-C02: sin un `TokenDeAcceso` válido, `/mcp` responde 401 y no ejecuta nada."""

from __future__ import annotations

import datetime as dt

import jwt
import pytest
from fastapi.testclient import TestClient

INITIALIZE_BODY = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "pytest", "version": "1"},
    },
}
TOOLS_LIST_BODY = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
CALL_TOOL_BODY = {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {"name": "list_novels", "arguments": {}},
}
MCP_ACCEPT = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}


def _expired_token() -> str:
    now = dt.datetime(2020, 1, 1, tzinfo=dt.UTC)
    payload = {
        "sub": "1",
        "iat": int(now.timestamp()),
        "exp": int(now.timestamp()) - 1,
        "aud": "access_token",
        "iss": "story-maker",
    }
    return jwt.encode(payload, "x" * 32, algorithm="HS256")


def _alg_none_token() -> str:
    payload = {"sub": "1", "aud": "access_token", "iss": "story-maker"}
    return jwt.encode(payload, "", algorithm="none")


@pytest.mark.parametrize("body", [INITIALIZE_BODY, TOOLS_LIST_BODY, CALL_TOOL_BODY])
@pytest.mark.parametrize(
    "headers",
    [
        None,
        {"Authorization": "Basic dXNlcjpwYXNz"},
        {"Authorization": "Bearer garbage-not-a-jwt"},
    ],
)
async def test_requests_without_a_valid_token_get_401_and_run_nothing(
    client: TestClient, raw_mcp_request, headers: dict[str, str] | None, body: dict[str, object]
) -> None:
    async with raw_mcp_request() as raw:
        response = await raw.post("/mcp", json=body, headers={**MCP_ACCEPT, **(headers or {})})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "no autorizado"}


async def test_expired_token_gets_401(client: TestClient, raw_mcp_request) -> None:
    headers = {**MCP_ACCEPT, "Authorization": f"Bearer {_expired_token()}"}
    async with raw_mcp_request() as raw:
        response = await raw.post("/mcp", json=INITIALIZE_BODY, headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "no autorizado"}


async def test_alg_none_token_gets_401(client: TestClient, raw_mcp_request) -> None:
    headers = {**MCP_ACCEPT, "Authorization": f"Bearer {_alg_none_token()}"}
    async with raw_mcp_request() as raw:
        response = await raw.post("/mcp", json=INITIALIZE_BODY, headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "no autorizado"}


async def test_view_token_of_own_version_gets_401(
    client: TestClient, raw_mcp_request, auth_headers: dict[str, str]
) -> None:
    """Un token de vista (`aud`=`view_token`) no sirve en `/mcp`: no es un `TokenDeAcceso`."""
    novel = client.post("/api/novels", headers=auth_headers).json()
    view_token = jwt.decode(
        auth_headers["Authorization"].removeprefix("Bearer "),
        options={"verify_signature": False},
    )
    payload = {**view_token, "aud": "view_token"}
    token = jwt.encode(payload, "x" * 32, algorithm="HS256")
    headers = {**MCP_ACCEPT, "Authorization": f"Bearer {token}"}
    async with raw_mcp_request() as raw:
        response = await raw.post("/mcp", json=INITIALIZE_BODY, headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "no autorizado"}
    assert novel["id"] >= 1

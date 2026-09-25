"""015-C10: una entrada fuera de schema es un error sin efecto."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from fastmcp.exceptions import ToolError
from sqlalchemy.orm import Session, sessionmaker
from tests.render.novela_fixture import Novela

from story_maker.store.models import AuditLog


def _fingerprint(client: TestClient, headers: dict[str, str]) -> object:
    return client.get("/api/novels", headers=headers).json()


def _audit_count(session_factory: sessionmaker[Session]) -> int:
    with session_factory() as session:
        return session.query(AuditLog).count()


@pytest.mark.parametrize(
    "arguments",
    [
        {"novel_id": 1, "version": 2},  # falta "chapter"
        {"novel_id": 1, "version": "dos", "chapter": 3},  # tipo equivocado
        {"novel_id": 1, "version": 2, "chapter": 0},  # fuera de 1-10
    ],
)
async def test_get_chapter_with_a_malformed_argument_is_a_schema_error_without_effect(
    client: TestClient,
    novela_p: Novela,
    novela_p_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    mcp_session,
    arguments: dict[str, object],
) -> None:
    arguments = {**arguments, "novel_id": novela_p.novel_id}
    before_db = _fingerprint(client, novela_p_headers)
    before_audit = _audit_count(session_factory)

    async with mcp_session(novela_p_headers) as session:
        with pytest.raises(ToolError):
            await session.call_tool("get_chapter", arguments)

    assert _fingerprint(client, novela_p_headers) == before_db
    assert _audit_count(session_factory) == before_audit


async def test_request_change_with_a_selection_that_is_neither_fragment_nor_fact_is_a_schema_error(
    client: TestClient,
    novela_p: Novela,
    novela_p_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    mcp_session,
) -> None:
    before_db = _fingerprint(client, novela_p_headers)
    before_audit = _audit_count(session_factory)

    async with mcp_session(novela_p_headers) as session:
        with pytest.raises(ToolError):
            await session.call_tool(
                "request_change",
                {
                    "novel_id": novela_p.novel_id,
                    "selection": {"type": "not_a_real_selection"},
                    "request": "algo",
                },
            )

    assert _fingerprint(client, novela_p_headers) == before_db
    assert _audit_count(session_factory) == before_audit


async def test_request_change_with_a_missing_argument_is_a_schema_error(
    client: TestClient,
    novela_p: Novela,
    novela_p_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    mcp_session,
) -> None:
    before_audit = _audit_count(session_factory)
    async with mcp_session(novela_p_headers) as session:
        with pytest.raises(ToolError):
            await session.call_tool(
                "request_change", {"novel_id": novela_p.novel_id, "request": "algo"}
            )
    assert _audit_count(session_factory) == before_audit

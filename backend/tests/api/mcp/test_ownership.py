"""015-C09: lo ajeno responde como inexistente en las siete tools."""

from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient
from fastmcp.exceptions import ToolError
from sqlalchemy.orm import Session, sessionmaker
from tests.render.novela_fixture import Novela

from story_maker.pipeline.changes.request import hash_code
from story_maker.store.models import ChangeRequest

MISSING_NOVEL_ID = 999_999
MISSING_REQUEST_ID = 999_999


def _status(exc: ToolError) -> int:
    import json

    return int(json.loads(str(exc))["status"])


@pytest.fixture
def proposed_change_request(
    session_factory: sessionmaker[Session], novela_p: Novela
) -> tuple[int, str]:
    """Una `SolicitudDeCambio` `proposed` de A sobre P, con su código, para 015-C09."""
    from story_maker.store.session import unit_of_work

    code = "el-codigo-de-a"
    with unit_of_work(session_factory) as uow:
        row = ChangeRequest(
            novel_id=novela_p.novel_id,
            base_version_id=novela_p.v2_id,
            selection_type="fact",
            selection={"type": "fact", "fact_id": 1},
            request="cambia el nombre",
            proposal={"changes": [], "new_fact": None},
            affected_chapters=[],
            code_hash=hash_code(code),
            expires_at=dt.datetime(2026, 9, 25, 12, 0),
            status="proposed",
            created_at=dt.datetime(2026, 9, 24, 12, 0),
            proposal_trace="t",
        )
        uow.add(row)
        uow.session.flush()
        request_id = row.id
    return request_id, code


READ_CALLS = [
    ("get_chapter", lambda novel_id: {"novel_id": novel_id, "version": 2, "chapter": 1}),
    ("list_versions", lambda novel_id: {"novel_id": novel_id}),
    ("query_story_bible", lambda novel_id: {"novel_id": novel_id, "version": 2}),
    ("download_novel", lambda novel_id: {"novel_id": novel_id, "version": 2}),
]


@pytest.mark.parametrize("tool", READ_CALLS, ids=[c[0] for c in READ_CALLS])
async def test_foreign_or_missing_novel_reads_answer_the_same_404(
    client: TestClient,
    novela_p: Novela,
    other_client_headers: dict[str, str],
    mcp_session,
    tool: tuple[str, object],
) -> None:
    name, args_of = tool
    async with mcp_session(other_client_headers) as session:
        with pytest.raises(ToolError) as foreign:
            await session.call_tool(name, args_of(novela_p.novel_id))
    async with mcp_session(other_client_headers) as session:
        with pytest.raises(ToolError) as missing:
            await session.call_tool(name, args_of(MISSING_NOVEL_ID))

    assert _status(foreign.value) == 404
    assert str(foreign.value) == str(missing.value)


async def test_list_novels_of_b_never_includes_as_novel(
    client: TestClient,
    novela_p: Novela,
    other_client_headers: dict[str, str],
    mcp_session,
) -> None:
    async with mcp_session(other_client_headers) as session:
        result = await session.call_tool("list_novels", {})
    novels = result.structured_content.get("result", result.structured_content)
    ids = {n["id"] for n in novels}
    assert novela_p.novel_id not in ids


async def test_request_change_on_a_foreign_novel_is_404_denies_without_a_session(
    client: TestClient,
    novela_p: Novela,
    other_client_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    mcp_session,
) -> None:
    from story_maker.store.models import AuditLog

    async with mcp_session(other_client_headers) as session:
        with pytest.raises(ToolError) as excinfo:
            await session.call_tool(
                "request_change",
                {
                    "novel_id": novela_p.novel_id,
                    "selection": {"type": "fact", "fact_id": 1},
                    "request": "algo",
                },
            )
    assert _status(excinfo.value) == 404

    with session_factory() as session:
        rows = session.query(AuditLog).filter(AuditLog.origin == "mcp_write").all()
    (row,) = [r for r in rows if r.tool == "request_change"]
    assert row.decision == "deny"
    assert row.novel_id is None


async def test_confirm_change_of_as_request_by_b_is_404_and_leaves_it_proposed(
    client: TestClient,
    novela_p: Novela,
    other_client_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    proposed_change_request: tuple[int, str],
    mcp_session,
) -> None:
    from story_maker.store.models import AuditLog

    request_id, code = proposed_change_request
    async with mcp_session(other_client_headers) as session:
        with pytest.raises(ToolError) as excinfo:
            await session.call_tool("confirm_change", {"request_id": request_id, "code": code})
    assert _status(excinfo.value) == 404

    with session_factory() as session:
        row = session.get(ChangeRequest, request_id)
        assert row is not None
        assert row.status == "proposed"
        assert row.run_id is None
        audit_rows = session.query(AuditLog).filter(AuditLog.origin == "mcp_write").all()
    (audit,) = [r for r in audit_rows if r.tool == "confirm_change"]
    assert audit.decision == "deny"
    assert audit.novel_id is None

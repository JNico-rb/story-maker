"""015-C16: cada llamada a una tool deja exactamente una traza `mcp:<tool>`."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from fastmcp.exceptions import ToolError
from tests.render.novela_fixture import Novela

from story_maker.observability.null import NullObservability


def _traces_named(telemetry: NullObservability, name: str) -> list:
    return [t for t in telemetry.traces.values() if t.name == name]


async def test_a_successful_call_leaves_exactly_one_trace_named_mcp_tool(
    client: TestClient,
    novela_p: Novela,
    novela_p_headers: dict[str, str],
    telemetry: NullObservability,
    mcp_session,
) -> None:
    async with mcp_session(novela_p_headers) as session:
        await session.call_tool("list_versions", {"novel_id": novela_p.novel_id})

    traces = _traces_named(telemetry, "mcp:list_versions")
    assert len(traces) == 1
    assert traces[0].session == str(novela_p.novel_id)


async def test_a_404_call_leaves_exactly_one_trace_without_a_session(
    client: TestClient,
    novela_p_headers: dict[str, str],
    telemetry: NullObservability,
    mcp_session,
) -> None:
    async with mcp_session(novela_p_headers) as session:
        with pytest.raises(ToolError):
            await session.call_tool("list_versions", {"novel_id": 999_999})

    traces = _traces_named(telemetry, "mcp:list_versions")
    assert len(traces) == 1
    assert traces[0].session is None
    (span,) = traces[0].spans
    assert span.level == "WARNING"
    assert span.status_message


async def test_a_schema_error_still_leaves_exactly_one_trace_without_a_session(
    client: TestClient,
    novela_p: Novela,
    novela_p_headers: dict[str, str],
    telemetry: NullObservability,
    mcp_session,
) -> None:
    async with mcp_session(novela_p_headers) as session:
        with pytest.raises(ToolError):
            await session.call_tool(
                "get_chapter", {"novel_id": novela_p.novel_id, "version": 1, "chapter": 0}
            )

    traces = _traces_named(telemetry, "mcp:get_chapter")
    assert len(traces) == 1
    assert traces[0].session is None


async def test_initialize_list_tools_and_a_401_leave_no_trace(
    client: TestClient, telemetry: NullObservability, raw_mcp_request
) -> None:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "pytest", "version": "1"},
        },
    }
    async with raw_mcp_request() as raw:
        await raw.post(
            "/mcp",
            json=body,
            headers={"Accept": "application/json, text/event-stream"},
        )

    assert telemetry.traces == {}

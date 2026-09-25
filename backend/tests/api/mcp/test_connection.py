"""015-C01: el servidor responde en `/mcp` y publica exactamente sus siete tools."""

from __future__ import annotations

from fastapi.testclient import TestClient

READ_ONLY_TOOLS = {
    "list_novels",
    "get_chapter",
    "list_versions",
    "query_story_bible",
    "download_novel",
}
WRITE_TOOLS = {"request_change", "confirm_change"}


async def test_server_answers_at_mcp_and_publishes_exactly_its_seven_tools(
    client: TestClient, auth_headers: dict[str, str], mcp_session
) -> None:
    async with mcp_session(auth_headers) as session:
        tools = await session.list_tools()
        resources = await session.list_resources()
        resource_templates = await session.list_resource_templates()
        prompts = await session.list_prompts()

        assert session.server_info is not None
        assert session.server_info.name == "story-maker"

    assert resources == []
    assert resource_templates == []
    assert prompts == []

    names = {tool.name for tool in tools}
    assert names == READ_ONLY_TOOLS | WRITE_TOOLS

    by_name = {tool.name: tool for tool in tools}
    for name in READ_ONLY_TOOLS | WRITE_TOOLS:
        tool = by_name[name]
        assert tool.description
        assert tool.input_schema
        if name != "download_novel":
            assert tool.output_schema

    for name in READ_ONLY_TOOLS:
        assert by_name[name].annotations is not None
        assert by_name[name].annotations.read_only_hint is True

    for name in WRITE_TOOLS:
        annotations = by_name[name].annotations
        assert annotations is not None
        assert annotations.read_only_hint is not True
        assert annotations.destructive_hint is not True

    # `/api` sigue respondiendo en la misma aplicación.
    health = client.get("/health")
    assert health.status_code == 200

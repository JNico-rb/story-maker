"""015-I5: el schema publicado de cada tool es el que se deriva de su modelo, y toda salida con
éxito lo cumple (`verification.md` §3.5). Cubre las salidas de 015-C04 a 015-C08, C11 y C13; las
cinco lecturas y las dos escrituras, cada una contra el `output_schema` que la tool publicó en
015-C01."""

from __future__ import annotations

from typing import Any

import jsonschema
import pytest
from fastapi.testclient import TestClient
from tests.api.change_requests.conftest import F, build_f, fact_selection, headers, propose, rename
from tests.render.novela_fixture import Novela

from story_maker.agents.fake import FakeAgent


@pytest.fixture
def f(session_factory) -> F:  # type: ignore[no-untyped-def]
    return build_f(session_factory)


def _validate(schema: dict[str, Any], instance: Any) -> None:
    jsonschema.validate(instance=instance, schema=schema)


async def test_every_successful_output_matches_its_published_schema(
    client: TestClient,
    novela_p: Novela,
    novela_p_headers: dict[str, str],
    f: F,
    fake: FakeAgent,
    mcp_session,
) -> None:
    async with mcp_session(novela_p_headers) as session:
        schemas = {tool.name: tool.output_schema for tool in await session.list_tools()}

        list_novels = await session.call_tool("list_novels", {})
        _validate(schemas["list_novels"], list_novels.structured_content)

        list_versions = await session.call_tool("list_versions", {"novel_id": novela_p.novel_id})
        _validate(schemas["list_versions"], list_versions.structured_content)

        get_chapter = await session.call_tool(
            "get_chapter", {"novel_id": novela_p.novel_id, "version": 1, "chapter": 1}
        )
        _validate(schemas["get_chapter"], get_chapter.structured_content)

        story_bible = await session.call_tool(
            "query_story_bible", {"novel_id": novela_p.novel_id, "version": 1}
        )
        _validate(schemas["query_story_bible"], story_bible.structured_content)

        download = await session.call_tool(
            "download_novel", {"novel_id": novela_p.novel_id, "version": 1}
        )
    assert schemas["download_novel"] is None
    (content,) = download.content
    assert content.type == "resource"
    assert content.resource.mime_type == "application/pdf"

    propose(fake, rename(f.toby_name_fact, "Luna"))
    async with mcp_session(headers(f.user_a)) as session:
        proposal = await session.call_tool(
            "request_change",
            {
                "novel_id": f.novel_id,
                "selection": fact_selection(f.toby_name_fact),
                "request": "el perro se llama Luna",
            },
        )
    _validate(schemas["request_change"], proposal.structured_content)

    async with mcp_session(headers(f.user_a)) as session:
        confirmation = await session.call_tool(
            "confirm_change",
            {
                "request_id": proposal.structured_content["id"],
                "code": proposal.structured_content["code"],
            },
        )
    _validate(schemas["confirm_change"], confirmation.structured_content)

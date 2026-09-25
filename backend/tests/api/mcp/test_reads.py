"""015-C04 a 015-C08: las cinco tools de lectura, sobre P (v1/v2 publicadas) y S (sin publicar)."""

from __future__ import annotations

import base64
import json

import pytest
from fastapi.testclient import TestClient
from fastmcp.exceptions import ToolError
from tests.render.novela_fixture import Novela


def _fingerprint(client: TestClient, headers: dict[str, str]) -> object:
    """Aproximación observable a «la huella de la base»: lo que el cliente puede leer no cambia
    (015-C04 a 015-C10 no dan otro punto de observación T sin acceso directo a SQLite)."""
    return client.get("/api/novels", headers=headers).json()


def _status(exc: ToolError) -> int:
    return int(json.loads(str(exc))["status"])


# --- 015-C04 · list_novels --------------------------------------------------------------------


async def test_list_novels_gives_the_clients_novels_with_status_and_current_version(
    client: TestClient,
    novela_p: Novela,
    novela_p_headers: dict[str, str],
    novel_s: int,
    other_client_headers: dict[str, str],
    mcp_session,
) -> None:
    before = _fingerprint(client, novela_p_headers)

    async with mcp_session(novela_p_headers) as session:
        result = await session.call_tool("list_novels", {})
    novels = getattr(result.data, "root", result.data)
    by_id = {n.id: n for n in novels}

    assert set(by_id) == {novela_p.novel_id, novel_s}
    assert by_id[novela_p.novel_id].status == "published"
    assert by_id[novela_p.novel_id].current_version == 2
    assert by_id[novel_s].status in ("interview", "ready")
    assert by_id[novel_s].current_version is None

    api_body = client.get("/api/novels", headers=novela_p_headers).json()
    assert {n["id"] for n in api_body} == set(by_id)

    async with mcp_session(other_client_headers) as session:
        empty = await session.call_tool("list_novels", {})
    assert list(getattr(empty.data, "root", empty.data)) == []

    assert _fingerprint(client, novela_p_headers) == before


# --- 015-C05 · list_versions ---------------------------------------------------------------


async def test_list_versions_gives_the_published_history_with_changed_chapters(
    client: TestClient,
    novela_p: Novela,
    novela_p_headers: dict[str, str],
    novel_s: int,
    mcp_session,
) -> None:
    before = _fingerprint(client, novela_p_headers)

    async with mcp_session(novela_p_headers) as session:
        result = await session.call_tool("list_versions", {"novel_id": novela_p.novel_id})
    versions = result.structured_content["versions"]
    assert [v["number"] for v in versions] == [1, 2]
    by_number = {v["number"]: v for v in versions}
    assert by_number[1]["changed_chapters"] == []
    assert by_number[2]["changed_chapters"] == [3, 7]

    api_body = client.get(
        f"/api/novels/{novela_p.novel_id}/versions", headers=novela_p_headers
    ).json()
    assert versions == api_body["versions"]

    async with mcp_session(novela_p_headers) as session:
        empty = await session.call_tool("list_versions", {"novel_id": novel_s})
    assert empty.structured_content["versions"] == []

    assert _fingerprint(client, novela_p_headers) == before


# --- 015-C06 · get_chapter -------------------------------------------------------------------


async def test_get_chapter_returns_a_chapter_of_a_published_version(
    client: TestClient, novela_p: Novela, novela_p_headers: dict[str, str], mcp_session
) -> None:
    before = _fingerprint(client, novela_p_headers)

    async def chapter(version: int, number: int) -> dict[str, object]:
        async with mcp_session(novela_p_headers) as session:
            result = await session.call_tool(
                "get_chapter",
                {"novel_id": novela_p.novel_id, "version": version, "chapter": number},
            )
        return result.structured_content

    cap3_v1 = await chapter(1, 3)
    cap3_v2 = await chapter(2, 3)
    assert cap3_v1["text"] != cap3_v2["text"]
    assert "Nala" in str(cap3_v2["text"])

    cap5_v1 = await chapter(1, 5)
    cap5_v2 = await chapter(2, 5)
    assert cap5_v1["text"] == cap5_v2["text"]

    assert (await chapter(1, 1))["number"] == 1
    assert (await chapter(1, 10))["number"] == 10

    assert _fingerprint(client, novela_p_headers) == before


@pytest.mark.parametrize("chapter_number", [0, 11])
async def test_get_chapter_out_of_range_is_a_schema_error(
    client: TestClient,
    novela_p: Novela,
    novela_p_headers: dict[str, str],
    mcp_session,
    chapter_number: int,
) -> None:
    async with mcp_session(novela_p_headers) as session:
        with pytest.raises(ToolError) as excinfo:
            await session.call_tool(
                "get_chapter",
                {"novel_id": novela_p.novel_id, "version": 1, "chapter": chapter_number},
            )
    assert "chapter" in str(excinfo.value)


async def test_get_chapter_of_a_candidate_version_is_404(
    client: TestClient, novela_p: Novela, novela_p_headers: dict[str, str], mcp_session
) -> None:
    async with mcp_session(novela_p_headers) as session:
        with pytest.raises(ToolError) as excinfo:
            await session.call_tool(
                "get_chapter", {"novel_id": novela_p.novel_id, "version": 3, "chapter": 1}
            )
    assert _status(excinfo.value) == 404


async def test_get_chapter_of_an_unpublished_novel_is_404(
    client: TestClient, novela_p_headers: dict[str, str], novel_s: int, mcp_session
) -> None:
    async with mcp_session(novela_p_headers) as session:
        with pytest.raises(ToolError) as excinfo:
            await session.call_tool(
                "get_chapter", {"novel_id": novel_s, "version": 1, "chapter": 1}
            )
    assert _status(excinfo.value) == 404


# --- 015-C07 · query_story_bible -------------------------------------------------------------


async def test_query_story_bible_gives_the_story_bible_of_a_version(
    client: TestClient, novela_p: Novela, novela_p_headers: dict[str, str], mcp_session
) -> None:
    before = _fingerprint(client, novela_p_headers)

    async def dog_name(version: int) -> str:
        async with mcp_session(novela_p_headers) as session:
            result = await session.call_tool(
                "query_story_bible", {"novel_id": novela_p.novel_id, "version": version}
            )
        facts = result.structured_content["story_bible"]["facts"]
        (dog,) = [f for f in facts if f["attribute"] == "name" and f["value"] in ("Toby", "Nala")]
        return str(dog["value"])

    assert await dog_name(1) == "Toby"
    assert await dog_name(2) == "Nala"

    api_body = client.get(
        f"/api/novels/{novela_p.novel_id}/story-bible?version=2", headers=novela_p_headers
    ).json()
    async with mcp_session(novela_p_headers) as session:
        mcp_body = await session.call_tool(
            "query_story_bible", {"novel_id": novela_p.novel_id, "version": 2}
        )
    assert mcp_body.structured_content["story_bible"] == api_body["story_bible"]

    assert _fingerprint(client, novela_p_headers) == before


async def test_query_story_bible_of_an_unpublished_version_is_404(
    client: TestClient, novela_p: Novela, novela_p_headers: dict[str, str], mcp_session
) -> None:
    async with mcp_session(novela_p_headers) as session:
        with pytest.raises(ToolError) as excinfo:
            await session.call_tool(
                "query_story_bible", {"novel_id": novela_p.novel_id, "version": 3}
            )
    assert _status(excinfo.value) == 404


# --- 015-C08 · download_novel ----------------------------------------------------------------


async def test_download_novel_gives_the_saved_pdf_as_an_embedded_resource(
    client: TestClient, novela_p: Novela, novela_p_headers: dict[str, str], mcp_session
) -> None:
    before = _fingerprint(client, novela_p_headers)

    async def pdf_bytes(version: int) -> bytes:
        async with mcp_session(novela_p_headers) as session:
            result = await session.call_tool(
                "download_novel", {"novel_id": novela_p.novel_id, "version": version}
            )
        (content,) = result.content
        assert content.type == "resource"
        resource = content.resource
        assert resource.mime_type == "application/pdf"
        return base64.b64decode(resource.blob)

    v1_pdf = await pdf_bytes(1)
    v2_pdf = await pdf_bytes(2)
    assert v1_pdf != v2_pdf

    api_v1 = client.get(f"/api/novels/{novela_p.novel_id}/versions/1/pdf", headers=novela_p_headers)
    assert v1_pdf == api_v1.content

    assert _fingerprint(client, novela_p_headers) == before


async def test_download_novel_of_an_unpublished_version_is_404(
    client: TestClient, novela_p: Novela, novela_p_headers: dict[str, str], mcp_session
) -> None:
    async with mcp_session(novela_p_headers) as session:
        with pytest.raises(ToolError) as excinfo:
            await session.call_tool("download_novel", {"novel_id": novela_p.novel_id, "version": 3})
    assert _status(excinfo.value) == 404

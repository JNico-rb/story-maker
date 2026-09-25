"""015-C03: la identidad es la del token de cada petición."""

from __future__ import annotations

from fastapi.testclient import TestClient


async def test_identity_follows_the_token_of_each_request_never_a_previous_one(
    client: TestClient,
    auth_headers: dict[str, str],
    other_client_headers: dict[str, str],
    mcp_session,
) -> None:
    novel_a = client.post("/api/novels", headers=auth_headers).json()
    novel_b = client.post("/api/novels", headers=other_client_headers).json()

    async def novel_ids(headers: dict[str, str]) -> set[int]:
        async with mcp_session(headers) as session:
            result = await session.call_tool("list_novels", {})
        novels = getattr(result.data, "root", result.data)
        return {n.id for n in novels}

    assert await novel_ids(auth_headers) == {novel_a["id"]}
    assert await novel_ids(other_client_headers) == {novel_b["id"]}
    assert await novel_ids(auth_headers) == {novel_a["id"]}

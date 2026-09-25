"""015-C11 a 015-C15: `request_change` y `confirm_change`, con los mismos dobles y el mismo
fixture F de 014 (mismo flujo que la API en los dos canales, 015-I6)."""

from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient
from fastmcp.exceptions import ToolError
from sqlalchemy.orm import Session, sessionmaker
from tests.api.change_requests.conftest import (
    F,
    build_f,
    fact_selection,
    headers,
    propose,
    rename,
)
from tests.pipeline.changes.conftest import version_fingerprint

from story_maker.agents.fake import Call, Fail, FakeAgent, Script
from story_maker.store.models import AuditLog, ChangeRequest, Run


def _status(exc: ToolError) -> int:
    import json

    return int(json.loads(str(exc))["status"])


@pytest.fixture
def f(session_factory: sessionmaker[Session]) -> F:
    return build_f(session_factory)


def _mcp_write_rows(session_factory: sessionmaker[Session], tool: str) -> list[AuditLog]:
    with session_factory() as session:
        return list(
            session.query(AuditLog)
            .filter(AuditLog.origin == "mcp_write", AuditLog.tool == tool)
            .all()
        )


# --- 015-C11 -------------------------------------------------------------------------------


async def test_request_change_proposes_the_same_as_the_api_and_only_proposes(
    client: TestClient,
    f: F,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    mcp_session,
) -> None:
    before = version_fingerprint(session_factory, f.v1_id)
    propose(fake, rename(f.toby_name_fact, "Luna"))

    async with mcp_session(headers(f.user_a)) as session:
        result = await session.call_tool(
            "request_change",
            {
                "novel_id": f.novel_id,
                "selection": fact_selection(f.toby_name_fact),
                "request": "el perro se llama Luna",
            },
        )
    body = result.structured_content

    assert body["proposal"] == {
        "changes": [{"fact_id": f.toby_name_fact, "old_value": "Toby", "new_value": "Luna"}],
        "new_fact": None,
    }
    assert body["affected_chapters"] == [2, 5, 7]
    assert "code" in body

    with session_factory() as session:
        row = session.get(ChangeRequest, body["id"])
        assert row is not None
        assert row.status == "proposed"
        assert row.base_version_id == f.v1_id
        run_count = session.query(Run).filter(Run.novel_id == f.novel_id).count()
    assert run_count == 0
    assert version_fingerprint(session_factory, f.v1_id) == before

    allow_rows = _mcp_write_rows(session_factory, "request_change")
    (allow,) = [r for r in allow_rows if r.novel_id == f.novel_id]
    assert allow.decision == "allow"


# --- 015-C12 -------------------------------------------------------------------------------


async def test_request_change_without_a_published_version_is_409(
    client: TestClient,
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
    mcp_session,
) -> None:
    from story_maker.store.models import Brief, Novel, User
    from story_maker.store.session import unit_of_work

    now = dt.datetime(2026, 9, 24, 12, 0)
    with unit_of_work(session_factory) as uow:
        user = User(email="sin-version@example.com", password_hash="h", created_at=now)
        uow.add(user)
        uow.session.flush()
        novel = Novel(user_id=user.id, title=None, embedding_model="m1", created_at=now)
        uow.add(novel)
        uow.session.flush()
        uow.add(Brief(novel_id=novel.id, content={}, status="confirmed"))
        user_id, novel_id = user.id, novel.id

    async with mcp_session(headers(user_id)) as session:
        with pytest.raises(ToolError) as excinfo:
            await session.call_tool(
                "request_change",
                {
                    "novel_id": novel_id,
                    "selection": {"type": "fragment", "version": 1, "chapter": 1, "quote": "x"},
                    "request": "algo",
                },
            )
    assert _status(excinfo.value) == 409


async def test_request_change_with_a_banned_entry_is_422_and_leaves_the_request_rejected(
    client: TestClient,
    f: F,
    session_factory: sessionmaker[Session],
    mcp_session,
) -> None:
    before = version_fingerprint(session_factory, f.v1_id)
    async with mcp_session(headers(f.user_a)) as session:
        with pytest.raises(ToolError) as excinfo:
            await session.call_tool(
                "request_change",
                {
                    "novel_id": f.novel_id,
                    "selection": fact_selection(f.toby_name_fact),
                    "request": "que sea un zoquete",
                },
            )
    assert _status(excinfo.value) == 422

    with session_factory() as session:
        rows = session.query(ChangeRequest).filter(ChangeRequest.novel_id == f.novel_id).all()
    (row,) = rows
    assert row.status == "rejected"
    assert version_fingerprint(session_factory, f.v1_id) == before


async def test_request_change_without_any_proposal_after_max_retries_is_422_and_stays_rejected(
    client: TestClient,
    f: F,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    mcp_session,
) -> None:
    before = version_fingerprint(session_factory, f.v1_id)
    for _ in range(5):
        fake.script("planner", "change", Script(steps=(Call("propose_change", {}),)))

    async with mcp_session(headers(f.user_a)) as session:
        with pytest.raises(ToolError) as excinfo:
            await session.call_tool(
                "request_change",
                {
                    "novel_id": f.novel_id,
                    "selection": fact_selection(f.toby_name_fact),
                    "request": "el perro se llama Luna",
                },
            )
    assert _status(excinfo.value) == 422

    with session_factory() as session:
        rows = session.query(ChangeRequest).filter(ChangeRequest.novel_id == f.novel_id).all()
    (row,) = rows
    assert row.status == "rejected"
    assert version_fingerprint(session_factory, f.v1_id) == before

    deny_rows = _mcp_write_rows(session_factory, "request_change")
    (deny,) = [r for r in deny_rows if r.novel_id == f.novel_id]
    assert deny.decision == "deny"


async def test_request_change_with_a_provider_failure_is_503_and_leaves_no_request(
    client: TestClient,
    f: F,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    mcp_session,
) -> None:
    before = version_fingerprint(session_factory, f.v1_id)
    fake.script("planner", "change", Script(steps=(Fail(),)))

    async with mcp_session(headers(f.user_a)) as session:
        with pytest.raises(ToolError) as excinfo:
            await session.call_tool(
                "request_change",
                {
                    "novel_id": f.novel_id,
                    "selection": fact_selection(f.toby_name_fact),
                    "request": "el perro se llama Luna",
                },
            )
    assert _status(excinfo.value) == 503

    with session_factory() as session:
        count = session.query(ChangeRequest).filter(ChangeRequest.novel_id == f.novel_id).count()
    assert count == 0
    assert version_fingerprint(session_factory, f.v1_id) == before

    deny_rows = _mcp_write_rows(session_factory, "request_change")
    (deny,) = [r for r in deny_rows if r.novel_id == f.novel_id]
    assert deny.decision == "deny"


# --- 015-C13 -------------------------------------------------------------------------------


async def test_confirm_change_with_the_code_enqueues_the_run(
    client: TestClient,
    f: F,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    mcp_session,
) -> None:
    before = version_fingerprint(session_factory, f.v1_id)
    propose(fake, rename(f.toby_name_fact, "Luna"))
    async with mcp_session(headers(f.user_a)) as session:
        proposal = (
            await session.call_tool(
                "request_change",
                {
                    "novel_id": f.novel_id,
                    "selection": fact_selection(f.toby_name_fact),
                    "request": "el perro se llama Luna",
                },
            )
        ).structured_content

    async with mcp_session(headers(f.user_a)) as session:
        confirmation = (
            await session.call_tool(
                "confirm_change", {"request_id": proposal["id"], "code": proposal["code"]}
            )
        ).structured_content

    assert "run_id" in confirmation

    with session_factory() as session:
        run = session.get(Run, confirmation["run_id"])
        assert run is not None
        assert run.type == "change_request"
        assert run.status == "queued"
        assert run.base_version_id == f.v1_id
        row = session.get(ChangeRequest, proposal["id"])
        assert row is not None
        assert row.status == "confirmed"

    allow_rows = _mcp_write_rows(session_factory, "confirm_change")
    (allow,) = [r for r in allow_rows if r.novel_id == f.novel_id]
    assert allow.decision == "allow"
    assert version_fingerprint(session_factory, f.v1_id) == before


async def test_the_same_flow_crosses_channels_api_proposes_mcp_confirms(
    client: TestClient,
    f: F,
    fake: FakeAgent,
    mcp_session,
) -> None:
    propose(fake, rename(f.toby_name_fact, "Luna"))
    api_response = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": "el perro se llama Luna"},
        headers=headers(f.user_a),
    )
    assert api_response.status_code == 201, api_response.text
    body = api_response.json()

    async with mcp_session(headers(f.user_a)) as session:
        confirmation = (
            await session.call_tool(
                "confirm_change", {"request_id": body["id"], "code": body["code"]}
            )
        ).structured_content
    assert "run_id" in confirmation


# --- 015-C14 -------------------------------------------------------------------------------


async def test_confirm_change_with_a_nonexistent_request_is_404(
    client: TestClient, f: F, session_factory: sessionmaker[Session], mcp_session
) -> None:
    before = version_fingerprint(session_factory, f.v1_id)
    async with mcp_session(headers(f.user_a)) as session:
        with pytest.raises(ToolError) as excinfo:
            await session.call_tool("confirm_change", {"request_id": 999_999, "code": "x"})
    assert _status(excinfo.value) == 404
    assert version_fingerprint(session_factory, f.v1_id) == before


async def test_confirm_change_with_the_wrong_code_is_422(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session], mcp_session
) -> None:
    before = version_fingerprint(session_factory, f.v1_id)
    propose(fake, rename(f.toby_name_fact, "Luna"))
    async with mcp_session(headers(f.user_a)) as session:
        proposal = (
            await session.call_tool(
                "request_change",
                {
                    "novel_id": f.novel_id,
                    "selection": fact_selection(f.toby_name_fact),
                    "request": "el perro se llama Luna",
                },
            )
        ).structured_content

    async with mcp_session(headers(f.user_a)) as session:
        with pytest.raises(ToolError) as excinfo:
            await session.call_tool(
                "confirm_change", {"request_id": proposal["id"], "code": "codigo-equivocado"}
            )
    assert _status(excinfo.value) == 422

    with session_factory() as session:
        row = session.get(ChangeRequest, proposal["id"])
        assert row is not None
        assert row.status == "proposed"
    assert version_fingerprint(session_factory, f.v1_id) == before


async def test_confirm_change_twice_with_the_used_code_is_409(
    client: TestClient, f: F, fake: FakeAgent, session_factory: sessionmaker[Session], mcp_session
) -> None:
    propose(fake, rename(f.toby_name_fact, "Luna"))
    async with mcp_session(headers(f.user_a)) as session:
        proposal = (
            await session.call_tool(
                "request_change",
                {
                    "novel_id": f.novel_id,
                    "selection": fact_selection(f.toby_name_fact),
                    "request": "el perro se llama Luna",
                },
            )
        ).structured_content

    async with mcp_session(headers(f.user_a)) as session:
        await session.call_tool(
            "confirm_change", {"request_id": proposal["id"], "code": proposal["code"]}
        )

    before = version_fingerprint(session_factory, f.v1_id)
    async with mcp_session(headers(f.user_a)) as session:
        with pytest.raises(ToolError) as excinfo:
            await session.call_tool(
                "confirm_change", {"request_id": proposal["id"], "code": proposal["code"]}
            )
    assert _status(excinfo.value) == 409
    assert version_fingerprint(session_factory, f.v1_id) == before

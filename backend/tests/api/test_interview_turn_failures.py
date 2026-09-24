"""Un turno fallido no se guarda (008-C07)."""

from __future__ import annotations

import asyncio
import dataclasses
import datetime as dt
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import Call, Fail, FakeAgent, Hang, Say, Script
from story_maker.agents.port import AgentPort
from story_maker.api.app import create_app
from story_maker.config import Config
from story_maker.observability.null import NullObservability
from story_maker.policy.real_engine import RealPolicyEngine
from story_maker.store.models import RoleSession

JWT_SECRET = "x" * 32
NOW = dt.datetime(2026, 9, 24, 12, 0, 0)


def _build(
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
    telemetry: NullObservability,
    workspace: Path,
    config: Config,
) -> tuple[TestClient, TokenCeiling]:
    ceiling = TokenCeiling(config.token_ceiling)
    policy = RealPolicyEngine(session_factory, base_url="http://127.0.0.1:8000")
    agent_port = AgentPort(
        agent=fake,
        config=config,
        ceiling=ceiling,
        policy=policy,
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace,
    )
    app = create_app(
        session_factory=session_factory,
        jwt_secret=JWT_SECRET,
        clock=lambda: NOW,
        agent_port=agent_port,
        telemetry=telemetry,
        config=config,
        workspace=workspace,
        policy=policy,
    )
    client = TestClient(app)
    client.post("/api/auth/register", json={"email": "cliente@example.com", "password": "x" * 8})
    token = client.post(
        "/api/auth/login", json={"email": "cliente@example.com", "password": "x" * 8}
    ).json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client, ceiling


def _assert_nothing_was_saved(
    client: TestClient, session_factory: sessionmaker[Session], novel_id: int
) -> None:
    messages = client.get(f"/api/novels/{novel_id}/interview/messages").json()
    assert messages == []
    brief = client.get(f"/api/novels/{novel_id}/brief").json()
    assert brief["content"]["recipient"]["name"] == ""


def test_a_provider_failure_answers_503_and_saves_an_infrastructure_failure_role_session(
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
    telemetry: NullObservability,
    workspace: Path,
    config: Config,
) -> None:
    client, _ceiling = _build(session_factory, fake, telemetry, workspace, config)
    novel_id = client.post("/api/novels", json={}).json()["id"]
    fake.script("interviewer", None, Script(steps=(Fail(),)))

    response = client.post(f"/api/novels/{novel_id}/interview/messages", json={"text": "hola"})

    assert response.status_code == 503
    _assert_nothing_was_saved(client, session_factory, novel_id)
    with session_factory() as session:
        rows = session.query(RoleSession).filter(RoleSession.novel_id == novel_id).all()
        assert len(rows) == 1
        assert rows[0].run_id is None
        assert rows[0].outcome == "infrastructure_failure"


def test_exhausting_max_turns_answers_503_and_saves_the_role_session(
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
    telemetry: NullObservability,
    workspace: Path,
    config: Config,
) -> None:
    roles = dict(config.roles)
    roles["interviewer"] = dataclasses.replace(roles["interviewer"], max_turns=1)
    tuned = dataclasses.replace(config, roles=roles)
    client, _ceiling = _build(session_factory, fake, telemetry, workspace, tuned)
    novel_id = client.post("/api/novels", json={}).json()["id"]
    fake.script(
        "interviewer",
        None,
        Script(steps=(Call("update_brief", {"name": "Marta"}), Say("Hola."))),
    )

    response = client.post(f"/api/novels/{novel_id}/interview/messages", json={"text": "hola"})

    assert response.status_code == 503
    _assert_nothing_was_saved(client, session_factory, novel_id)
    with session_factory() as session:
        rows = session.query(RoleSession).filter(RoleSession.novel_id == novel_id).all()
        assert rows[0].outcome == "turns_exhausted"


def test_exhausting_the_session_timeout_answers_503_and_saves_the_role_session(
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
    telemetry: NullObservability,
    workspace: Path,
    config: Config,
) -> None:
    tuned = dataclasses.replace(config, session_timeout_seconds=1)
    client, _ceiling = _build(session_factory, fake, telemetry, workspace, tuned)
    novel_id = client.post("/api/novels", json={}).json()["id"]
    fake.script("interviewer", None, Script(steps=(Hang(result=True),)))

    response = client.post(f"/api/novels/{novel_id}/interview/messages", json={"text": "hola"})

    assert response.status_code == 503
    _assert_nothing_was_saved(client, session_factory, novel_id)
    with session_factory() as session:
        rows = session.query(RoleSession).filter(RoleSession.novel_id == novel_id).all()
        assert rows[0].outcome == "time_exhausted"


def test_a_session_that_ends_without_a_reply_answers_503_and_saves_the_role_session(
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
    telemetry: NullObservability,
    workspace: Path,
    config: Config,
) -> None:
    client, _ceiling = _build(session_factory, fake, telemetry, workspace, config)
    novel_id = client.post("/api/novels", json={}).json()["id"]
    fake.script("interviewer", None, Script(steps=(Call("update_brief", {"name": "Marta"}),)))

    response = client.post(f"/api/novels/{novel_id}/interview/messages", json={"text": "hola"})

    assert response.status_code == 503
    _assert_nothing_was_saved(client, session_factory, novel_id)
    with session_factory() as session:
        rows = session.query(RoleSession).filter(RoleSession.novel_id == novel_id).all()
        assert rows[0].outcome == "completed"


def test_no_room_in_the_ceiling_within_the_wait_answers_503_and_opens_no_session(
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
    telemetry: NullObservability,
    workspace: Path,
    config: Config,
) -> None:
    tuned = dataclasses.replace(config, api_wait_seconds=1)
    client, ceiling = _build(session_factory, fake, telemetry, workspace, tuned)
    novel_id = client.post("/api/novels", json={}).json()["id"]
    fake.script("interviewer", None, Script(steps=(Call("update_brief", {"name": "Marta"}),)))

    blocker = asyncio.new_event_loop()
    ticket = blocker.run_until_complete(ceiling.acquire(ceiling.limit, None))
    try:
        response = client.post(f"/api/novels/{novel_id}/interview/messages", json={"text": "hola"})
    finally:
        ceiling.release(ticket)
        blocker.close()

    assert response.status_code == 503
    _assert_nothing_was_saved(client, session_factory, novel_id)
    with session_factory() as session:
        assert session.query(RoleSession).filter(RoleSession.novel_id == novel_id).count() == 0


def test_a_reservation_that_never_fits_answers_422_and_opens_no_session(
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
    telemetry: NullObservability,
    workspace: Path,
    config: Config,
) -> None:
    tuned = dataclasses.replace(config, token_ceiling=1)
    client, _ceiling = _build(session_factory, fake, telemetry, workspace, tuned)
    novel_id = client.post("/api/novels", json={}).json()["id"]
    fake.script("interviewer", None, Script(steps=(Call("update_brief", {"name": "Marta"}),)))

    response = client.post(f"/api/novels/{novel_id}/interview/messages", json={"text": "hola"})

    assert response.status_code == 422
    _assert_nothing_was_saved(client, session_factory, novel_id)
    with session_factory() as session:
        assert session.query(RoleSession).filter(RoleSession.novel_id == novel_id).count() == 0

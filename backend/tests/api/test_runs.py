"""`/api/novels/{id}/runs` y `/api/runs/{id}` (011-C01, C02, C04)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.api.app import create_app
from story_maker.api.auth import create_access_token
from story_maker.store.models import Brief, Novel, Run, User, Version
from story_maker.store.session import create_schema, make_engine, make_session_factory

JWT_SECRET = "x" * 32
NOW = dt.datetime(2026, 9, 24, 11, 0)


@pytest.fixture
def session_factory(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = make_engine(tmp_path / "story-maker.db")
    create_schema(engine)
    yield make_session_factory(engine)
    engine.dispose()


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> TestClient:
    return TestClient(
        create_app(session_factory=session_factory, jwt_secret=JWT_SECRET, clock=lambda: NOW)
    )


def headers(user_id: int) -> dict[str, str]:
    token = create_access_token(user_id, JWT_SECRET, 24, NOW)
    return {"Authorization": f"Bearer {token}"}


def add_user(session_factory: sessionmaker[Session], email: str) -> int:
    with session_factory() as session:
        user = User(email=email, password_hash="x", created_at=NOW)
        session.add(user)
        session.commit()
        return user.id


def add_novel(
    session_factory: sessionmaker[Session], user_id: int, brief: str = "confirmed"
) -> int:
    with session_factory() as session:
        novel = Novel(user_id=user_id, title=None, embedding_model="e5", created_at=NOW)
        session.add(novel)
        session.flush()
        session.add(Brief(novel_id=novel.id, content={}, status=brief))
        session.commit()
        return novel.id


def add_run(
    session_factory: sessionmaker[Session],
    novel_id: int,
    status: str,
    created_at: dt.datetime = NOW,
    **fields: object,
) -> int:
    with session_factory() as session:
        values: dict[str, object] = {"phase": None, "resumes": 0, **fields}
        run = Run(
            novel_id=novel_id, type="generation", status=status, created_at=created_at, **values
        )
        session.add(run)
        session.commit()
        return run.id


def test_launching_the_generation_enqueues_it(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    owner = add_user(session_factory, "cliente@example.com")
    other = add_user(session_factory, "otro@example.com")
    for k in range(2):
        add_run(session_factory, add_novel(session_factory, other), "queued", NOW.replace(hour=k))
    novel_id = add_novel(session_factory, owner)

    response = client.post(f"/api/novels/{novel_id}/runs", headers=headers(owner))

    assert response.status_code == 202, response.text
    body = response.json()
    assert body["position"] == 3
    with session_factory() as session:
        run = session.get(Run, body["run_id"])
        assert run is not None
        assert (run.novel_id, run.type, run.status, run.phase) == (
            novel_id,
            "generation",
            "queued",
            None,
        )
        assert run.created_at == NOW
        assert run.candidate_version_id is None


def add_published(session_factory: sessionmaker[Session], novel_id: int) -> None:
    with session_factory() as session:
        session.add(
            Version(
                novel_id=novel_id,
                status="published",
                number=1,
                published_at=NOW,
                changed_chapters=[],
                created_at=NOW,
            )
        )
        session.commit()


def run_count(session_factory: sessionmaker[Session]) -> int:
    with session_factory() as session:
        return session.query(Run).count()


@pytest.mark.parametrize(
    "situation",
    ["draft brief", "queued", "running", "interrupted", "published version"],
)
def test_a_generation_is_only_launched_from_a_ready_novel(
    situation: str, client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    owner = add_user(session_factory, "cliente@example.com")
    novel_id = add_novel(
        session_factory, owner, "draft" if situation == "draft brief" else "confirmed"
    )
    if situation in ("queued", "running", "interrupted"):
        add_run(session_factory, novel_id, situation)
    if situation == "published version":
        add_published(session_factory, novel_id)
    before = run_count(session_factory)

    response = client.post(f"/api/novels/{novel_id}/runs", headers=headers(owner))

    assert response.status_code == 409, response.text
    assert run_count(session_factory) == before


def test_a_novel_whose_only_generation_failed_can_launch_again(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    owner = add_user(session_factory, "cliente@example.com")
    novel_id = add_novel(session_factory, owner)
    failed = add_run(session_factory, novel_id, "failed", reason="retries_exhausted")

    response = client.post(f"/api/novels/{novel_id}/runs", headers=headers(owner))

    assert response.status_code == 202, response.text
    assert response.json()["run_id"] != failed
    assert run_count(session_factory) == 2


def test_launching_on_a_foreign_or_missing_novel_is_404_and_without_token_401(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    owner = add_user(session_factory, "cliente@example.com")
    stranger = add_user(session_factory, "otro@example.com")
    novel_id = add_novel(session_factory, owner)

    assert client.post(f"/api/novels/{novel_id}/runs", headers=headers(stranger)).status_code == 404
    assert client.post("/api/novels/999/runs", headers=headers(owner)).status_code == 404
    assert client.post(f"/api/novels/{novel_id}/runs").status_code == 401
    assert run_count(session_factory) == 0

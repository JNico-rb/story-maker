"""`/api/novels/{id}/runs`, `/api/runs/{id}` y `/api/runs/{id}/resume` (011-C01, C02, C04, C26)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.api.app import create_app
from story_maker.api.auth import create_access_token
from story_maker.pipeline.worker import Worker
from story_maker.store.models import Brief, Novel, RoleSession, Run, User, Version
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


def add_session(session_factory: sessionmaker[Session], run_id: int, cost: float | None) -> None:
    with session_factory() as session:
        run = session.get_one(Run, run_id)
        session.add(
            RoleSession(
                novel_id=run.novel_id,
                run_id=run_id,
                role="writer",
                chapter=4,
                model="modelo",
                reserved_tokens=1000,
                cost_usd=cost,
                latency_ms=10,
                outcome="completed" if cost is not None else "infrastructure_failure",
            )
        )
        session.commit()


def test_progress_is_polled_with_type_status_phase_chapter_cost_position_and_reason(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    owner = add_user(session_factory, "cliente@example.com")
    stranger = add_user(session_factory, "otro@example.com")
    first = add_run(session_factory, add_novel(session_factory, stranger), "queued")
    second = add_run(
        session_factory, add_novel(session_factory, owner), "queued", NOW.replace(hour=12)
    )
    running = add_run(
        session_factory, add_novel(session_factory, owner), "running", phase="writing", chapter=4
    )
    add_session(session_factory, running, 0.5)
    add_session(session_factory, running, 0.25)
    add_session(session_factory, running, None)
    interrupted = add_run(
        session_factory,
        add_novel(session_factory, owner),
        "interrupted",
        reason="provider_error",
        reason_detail="capítulo 6: error del proveedor",
    )

    def poll(run_id: int) -> dict[str, object]:
        response = client.get(f"/api/runs/{run_id}", headers=headers(owner))
        assert response.status_code == 200, response.text
        body: dict[str, object] = response.json()
        return body

    assert poll(second) == {
        "run_id": second,
        "type": "generation",
        "status": "queued",
        "phase": None,
        "chapter": None,
        "cost_usd": 0.0,
        "position": 2,
        "reason": None,
        "reason_detail": None,
    }
    progress = poll(running)
    assert (progress["phase"], progress["chapter"], progress["position"]) == ("writing", 4, None)
    assert progress["cost_usd"] == pytest.approx(0.75)
    assert progress["reason"] is None
    stopped = poll(interrupted)
    assert (stopped["reason"], stopped["reason_detail"]) == (
        "provider_error",
        "capítulo 6: error del proveedor",
    )
    assert stopped["position"] is None
    assert client.get(f"/api/runs/{first}", headers=headers(owner)).status_code == 404
    assert client.get("/api/runs/999", headers=headers(owner)).status_code == 404


def run_state(session_factory: sessionmaker[Session], run_id: int) -> tuple[str, int, dt.datetime]:
    with session_factory() as session:
        run = session.get_one(Run, run_id)
        return run.status, run.resumes, run.created_at


async def test_resuming_requeues_the_run_in_its_original_place(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    owner = add_user(session_factory, "cliente@example.com")
    t1, t2, t3 = (NOW + dt.timedelta(minutes=k) for k in (1, 2, 3))
    a = add_run(
        session_factory,
        add_novel(session_factory, owner),
        "interrupted",
        t1,
        reason="crash",
        reason_detail="el servidor se detuvo",
    )
    b = add_run(session_factory, add_novel(session_factory, owner), "running", t2)
    c = add_run(session_factory, add_novel(session_factory, owner), "queued", t3)

    response = client.post(f"/api/runs/{a}/resume", headers=headers(owner))

    assert response.status_code == 202, response.text
    assert response.json() == {"run_id": a, "position": 1}
    assert run_state(session_factory, a) == ("queued", 1, t1)
    taken: list[int] = []

    async def execute(run_id: int) -> None:
        taken.append(run_id)

    worker = Worker(session_factory, execute, max_resumes=2, clock=lambda: NOW)
    assert await worker.run_next() is None
    with session_factory() as session:
        session.get_one(Run, b).status = "published"
        session.commit()
    assert await worker.run_next() == a
    assert run_state(session_factory, c)[0] == "queued"


@pytest.mark.parametrize("status", ["queued", "running", "published", "failed"])
def test_resuming_a_run_that_is_not_interrupted_is_409_and_changes_nothing(
    status: str, client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    owner = add_user(session_factory, "cliente@example.com")
    run_id = add_run(session_factory, add_novel(session_factory, owner), status)
    before = run_state(session_factory, run_id)

    response = client.post(f"/api/runs/{run_id}/resume", headers=headers(owner))

    assert response.status_code == 409, response.text
    assert run_state(session_factory, run_id) == before


def test_resuming_a_foreign_run_is_404(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    owner = add_user(session_factory, "cliente@example.com")
    stranger = add_user(session_factory, "otro@example.com")
    run_id = add_run(session_factory, add_novel(session_factory, owner), "interrupted")

    response = client.post(f"/api/runs/{run_id}/resume", headers=headers(stranger))

    assert response.status_code == 404
    assert run_state(session_factory, run_id)[0] == "interrupted"

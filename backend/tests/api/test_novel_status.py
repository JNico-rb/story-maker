"""Lista y detalle de las novelas con su estado derivado (008-C02)."""

from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.store.models import Brief, Novel, Run, User, Version

NOW = dt.datetime(2026, 9, 24, 12, 0)


def _make_novel(
    session: Session, user_id: int, *, brief_status: str, title: str | None = None
) -> int:
    novel = Novel(user_id=user_id, title=title, embedding_model="m", created_at=NOW)
    session.add(novel)
    session.flush()
    session.add(Brief(novel_id=novel.id, content={}, status=brief_status))
    return novel.id


def _user_id(session: Session, email: str = "cliente@example.com") -> int:
    user = session.query(User).filter(User.email == email).one()
    return user.id


@pytest.mark.parametrize(
    ("brief_status", "runs", "published", "expected_status", "expected_version"),
    [
        ("draft", [], [], "interview", None),
        ("confirmed", [], [], "ready", None),
        ("confirmed", [("failed",)], [], "ready", None),
        ("confirmed", [("queued",)], [], "in_progress", None),
        ("confirmed", [("running",)], [], "in_progress", None),
        ("confirmed", [("interrupted",)], [], "in_progress", None),
        ("confirmed", [], [1, 2], "published", 2),
        ("confirmed", [("running", "change_request")], [1], "published", 1),
    ],
)
def test_a_novels_status_and_current_version_are_derived_from_runs_and_versions(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    brief_status: str,
    runs: list[tuple[str, ...]],
    published: list[int],
    expected_status: str,
    expected_version: int | None,
) -> None:
    client.get("/api/novels", headers=auth_headers)  # asegura que el cliente ya existe

    with session_factory() as session:
        user_id = _user_id(session)
        novel_id = _make_novel(session, user_id, brief_status=brief_status)
        for run_status, *rest in runs:
            run_type = rest[0] if rest else "generation"
            session.add(
                Run(
                    novel_id=novel_id,
                    type=run_type,
                    status=run_status,
                    resumes=0,
                    created_at=NOW,
                )
            )
        for number in published:
            session.add(
                Version(
                    novel_id=novel_id,
                    status="published",
                    number=number,
                    changed_chapters=[],
                    created_at=NOW,
                    published_at=NOW,
                )
            )
        session.commit()

    detail = client.get(f"/api/novels/{novel_id}", headers=auth_headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["status"] == expected_status
    assert body["current_version"] == expected_version


def test_the_list_goes_from_newest_to_oldest_and_only_shows_the_clients_own_novels(
    client: TestClient,
    auth_headers: dict[str, str],
    other_client_headers: dict[str, str],
    session_factory: sessionmaker[Session],
) -> None:
    client.get("/api/novels", headers=auth_headers)
    client.get("/api/novels", headers=other_client_headers)

    with session_factory() as session:
        mine = _user_id(session)
        other = _user_id(session, "otro@example.com")
        first = _make_novel(session, mine, brief_status="draft", title=None)
        session.commit()
        older = session.get(Novel, first)
        assert older is not None
        older.created_at = NOW - dt.timedelta(days=1)
        newer_id = _make_novel(session, mine, brief_status="draft")
        _make_novel(session, other, brief_status="draft")
        session.commit()

    response = client.get("/api/novels", headers=auth_headers)
    assert response.status_code == 200
    ids = [row["id"] for row in response.json()]
    assert ids == [newer_id, first]


def test_latest_run_id_is_the_most_recent_run_of_any_type_and_status_or_null_without_one(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    client.get("/api/novels", headers=auth_headers)  # asegura que el cliente ya existe

    with session_factory() as session:
        user_id = _user_id(session)
        novel_id = _make_novel(session, user_id, brief_status="confirmed")
        session.commit()

    detail = client.get(f"/api/novels/{novel_id}", headers=auth_headers)
    assert detail.json()["latest_run_id"] is None

    with session_factory() as session:
        older = Run(
            novel_id=novel_id, type="generation", status="failed", resumes=0, created_at=NOW
        )
        session.add(older)
        session.flush()
        newer = Run(
            novel_id=novel_id,
            type="change_request",
            status="queued",
            resumes=0,
            created_at=NOW + dt.timedelta(minutes=5),
        )
        session.add(newer)
        session.commit()
        newer_id = newer.id

    detail = client.get(f"/api/novels/{novel_id}", headers=auth_headers)
    assert detail.json()["latest_run_id"] == newer_id

    listing = client.get("/api/novels", headers=auth_headers)
    row = next(row for row in listing.json() if row["id"] == novel_id)
    assert row["latest_run_id"] == newer_id


def test_the_recipient_name_shows_once_the_brief_has_one(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    client.get("/api/novels", headers=auth_headers)
    with session_factory() as session:
        user_id = _user_id(session)
        novel = Novel(user_id=user_id, title=None, embedding_model="m", created_at=NOW)
        session.add(novel)
        session.flush()
        session.add(
            Brief(novel_id=novel.id, content={"recipient": {"name": "Marta"}}, status="draft")
        )
        session.commit()
        novel_id = novel.id

    response = client.get(f"/api/novels/{novel_id}", headers=auth_headers)
    assert response.json()["recipient_name"] == "Marta"

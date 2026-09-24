"""`GET /view/versions/{version_id}` exige el token de vista antes de nada más: nunca revela si
la versión existe (013-C07, 013-I2)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.api.app import create_app
from story_maker.api.auth import create_access_token
from story_maker.api.view_tokens import create_view_token
from story_maker.store.session import create_schema, make_engine, make_session_factory

JWT_SECRET = "x" * 32
SESSION_TIMEOUT_SECONDS = 600
V1 = 1
V2 = 2


class FakeClock:
    def __init__(self, now: dt.datetime) -> None:
        self._now = now

    def __call__(self) -> dt.datetime:
        return self._now

    def set(self, now: dt.datetime) -> None:
        self._now = now


@pytest.fixture
def session_factory(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = make_engine(tmp_path / "story-maker.db")
    create_schema(engine)
    yield make_session_factory(engine)
    engine.dispose()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.UTC))


@pytest.fixture
def client(session_factory: sessionmaker[Session], clock: FakeClock) -> TestClient:
    app = create_app(session_factory=session_factory, jwt_secret=JWT_SECRET, clock=clock)
    return TestClient(app)


def _valid_v1_token(clock: FakeClock) -> str:
    return create_view_token(V1, JWT_SECRET, SESSION_TIMEOUT_SECONDS, clock())


def test_an_invalid_view_token_answers_401_without_revealing_whether_the_version_exists(
    client: TestClient, clock: FakeClock
) -> None:
    valid_for_v1 = _valid_v1_token(clock)

    presented_for_another_version = client.get(f"/view/versions/{V2}?token={valid_for_v1}")

    access_token_instead_of_view = client.get(
        f"/view/versions/{V1}?token={create_access_token(1, JWT_SECRET, 24, clock())}"
    )

    timeout = dt.timedelta(seconds=SESSION_TIMEOUT_SECONDS)
    clock.set(clock() + timeout)
    used_after_timeout = client.get(f"/view/versions/{V1}?token={valid_for_v1}")
    clock.set(clock() - timeout)

    header_b64, payload_b64, sig_b64 = valid_for_v1.split(".")
    last_char = sig_b64[-1]
    tampered_sig = sig_b64[:-1] + ("A" if last_char != "A" else "B")
    tampered_signature = client.get(
        f"/view/versions/{V1}?token={header_b64}.{payload_b64}.{tampered_sig}"
    )

    missing_token = client.get(f"/view/versions/{V1}")

    responses = [
        presented_for_another_version,
        access_token_instead_of_view,
        used_after_timeout,
        tampered_signature,
        missing_token,
    ]
    for response in responses:
        assert response.status_code == 401, response.text
    bodies = {response.text for response in responses}
    assert len(bodies) == 1

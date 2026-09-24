"""`story-maker resume <run_id>` (011-C26)."""

from __future__ import annotations

import datetime as dt
import socket
from pathlib import Path

import pytest
from typer.testing import CliRunner

import story_maker.settings as settings_module
from story_maker.cli import app
from story_maker.store.models import Brief, Novel, Run, User
from story_maker.store.session import create_schema, make_engine, make_session_factory

NOW = dt.datetime(2026, 9, 24, 11, 0)
runner = CliRunner()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(settings_module, "ROOT", tmp_path)
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("FORMAL_VERIFIER", "local")
    monkeypatch.setenv("STORY_MAKER_BASE_URL", f"http://127.0.0.1:{_free_port()}")
    path = tmp_path / "backend" / "data" / "story-maker.db"
    path.parent.mkdir(parents=True)
    engine = make_engine(path)
    create_schema(engine)
    engine.dispose()
    return path


def add_run(db_path: Path, status: str, created_at: dt.datetime = NOW) -> int:
    engine = make_engine(db_path)
    try:
        with make_session_factory(engine)() as session:
            user = User(
                email=f"{status}{created_at:%M}@example.com", password_hash="x", created_at=NOW
            )
            session.add(user)
            session.flush()
            novel = Novel(user_id=user.id, title=None, embedding_model="e5", created_at=NOW)
            session.add(novel)
            session.flush()
            session.add(Brief(novel_id=novel.id, content={}, status="confirmed"))
            run = Run(
                novel_id=novel.id,
                type="generation",
                status=status,
                phase="writing" if status != "queued" else None,
                chapter=3 if status != "queued" else None,
                resumes=0,
                created_at=created_at,
                reason="crash" if status == "interrupted" else None,
            )
            session.add(run)
            session.commit()
            return run.id
    finally:
        engine.dispose()


def state(db_path: Path, run_id: int) -> tuple[str, int, str | None]:
    engine = make_engine(db_path)
    try:
        with make_session_factory(engine)() as session:
            run = session.get_one(Run, run_id)
            return run.status, run.resumes, run.reason
    finally:
        engine.dispose()


def test_resume_requeues_an_interrupted_run_in_its_place(db_path: Path) -> None:
    interrupted = add_run(db_path, "interrupted", NOW)
    later = add_run(db_path, "queued", NOW + dt.timedelta(minutes=5))

    result = runner.invoke(app, ["resume", str(interrupted)])

    assert result.exit_code == 0, result.output
    assert "posición 1" in result.output
    assert state(db_path, interrupted) == ("queued", 1, None)
    assert state(db_path, later)[0] == "queued"


@pytest.mark.parametrize("status", ["queued", "running", "published", "failed"])
def test_resume_of_a_run_that_is_not_interrupted_fails_and_changes_nothing(
    status: str, db_path: Path
) -> None:
    run_id = add_run(db_path, status)
    before = state(db_path, run_id)

    result = runner.invoke(app, ["resume", str(run_id)])

    assert result.exit_code != 0
    assert "interrupted" in result.output
    assert state(db_path, run_id) == before


def test_resume_of_a_missing_run_fails_with_a_message(db_path: Path) -> None:
    result = runner.invoke(app, ["resume", "999"])

    assert result.exit_code != 0
    assert "999" in result.output

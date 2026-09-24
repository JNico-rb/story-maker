"""`story-maker interview` (029-C01, C05, C06, C07): la entrevista de la 008 por terminal, en el
mismo proceso, con el doble falso del puerto de agente y el nulo de observabilidad."""

from __future__ import annotations

import datetime as dt
import json
import socket
from pathlib import Path

import pytest
from typer.testing import CliRunner

import story_maker.cli as cli_module
import story_maker.settings as settings_module
from story_maker.agents.fake import FakeAgent, Say, Script
from story_maker.cli import app
from story_maker.store.models import Interview, InterviewMessage, User
from story_maker.store.session import make_engine, make_session_factory

REAL_ROOT = settings_module.ROOT
REAL_CONFIG = json.loads((REAL_ROOT / "config.json").read_text(encoding="utf-8"))
EMAIL = "cliente@example.com"

runner = CliRunner()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture
def isolated_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Una raíz de proyecto sin `.env`, con `config.json` real y el `harness_workspace` mínimo
    de las pruebas de la 008 (interviewer y extractor)."""
    monkeypatch.setattr(settings_module, "ROOT", tmp_path)
    (tmp_path / "config.json").write_text(json.dumps(REAL_CONFIG), encoding="utf-8")
    workspace = tmp_path / "backend" / "harness_workspace"
    (workspace / "prompts").mkdir(parents=True)
    (workspace / "CLAUDE.md").write_text("Escribe en español.", encoding="utf-8")
    (workspace / "prompts" / "interviewer.md").write_text(
        "Eres el entrevistador.", encoding="utf-8"
    )
    (workspace / "prompts" / "extractor.md").write_text("Eres el extractor.", encoding="utf-8")
    return tmp_path


@pytest.fixture
def base_env(monkeypatch: pytest.MonkeyPatch, isolated_root: Path) -> Path:
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("FORMAL_VERIFIER", "local")
    monkeypatch.setenv("STORY_MAKER_BASE_URL", f"http://127.0.0.1:{_free_port()}")
    return isolated_root


@pytest.fixture
def db_path(base_env: Path) -> Path:
    result = runner.invoke(app, ["init-db"])
    assert result.exit_code == 0
    return base_env / "backend" / "data" / "story-maker.db"


@pytest.fixture
def registered_client(db_path: Path) -> Path:
    engine = make_engine(db_path)
    session = make_session_factory(engine)()
    session.add(User(email=EMAIL, password_hash="h", created_at=dt.datetime(2026, 1, 1)))
    session.commit()
    session.close()
    engine.dispose()
    return db_path


@pytest.fixture
def fake_agent(monkeypatch: pytest.MonkeyPatch) -> FakeAgent:
    fake = FakeAgent()
    monkeypatch.setattr(cli_module, "_build_agent", lambda settings, workspace: fake)
    return fake


def _session(db_path: Path):  # type: ignore[no-untyped-def]
    engine = make_engine(db_path)
    session = make_session_factory(engine)()
    return session, engine


# --- 029-C01: entrevistar una novela nueva ---------------------------------------------------


def test_interview_creates_a_novel_and_prints_its_id_and_reply(
    registered_client: Path, fake_agent: FakeAgent
) -> None:
    fake_agent.script("interviewer", None, Script(steps=(Say("¿Cómo se llama?"),)))

    result = runner.invoke(app, ["interview", "--email", EMAIL], input="Hola\n/salir\n")

    assert result.exit_code == 0, result.stdout
    lines = result.stdout.strip().splitlines()
    novel_id = int(lines[0])
    assert lines[-1] == "¿Cómo se llama?"

    session, engine = _session(registered_client)
    try:
        interview = session.query(Interview).filter(Interview.novel_id == novel_id).one()
        messages = (
            session.query(InterviewMessage)
            .filter(InterviewMessage.interview_id == interview.id)
            .order_by(InterviewMessage.id)
            .all()
        )
        assert [m.author for m in messages] == ["user", "interviewer"]
        assert messages[0].text == "Hola"
        assert messages[1].text == "¿Cómo se llama?"
    finally:
        session.close()
        engine.dispose()

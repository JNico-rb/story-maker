"""`story-maker evals run` (020-C02, 020-C05) y la validez de los briefs de evals (020-C01)."""

from __future__ import annotations

import datetime as dt
import json
import socket
from pathlib import Path

import pytest
from typer.testing import CliRunner

import story_maker.settings as settings_module
from story_maker.cli import EVAL_BRIEF_SLUGS, EVAL_BRIEFS_DIR, EVAL_MAX_MANDATORY_ELEMENTS, app
from story_maker.cli import eval_brief_content as _eval_brief_content
from story_maker.domain.brief import BriefContent, brief_problems
from story_maker.store import models
from story_maker.store.session import create_schema, make_engine, make_session_factory

NOW = dt.datetime(2026, 9, 24, 11, 0)
CREATED_AT = NOW.date()
runner = CliRunner()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture
def isolated_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(settings_module, "ROOT", tmp_path)
    return tmp_path


@pytest.fixture
def base_env(monkeypatch: pytest.MonkeyPatch, isolated_root: Path) -> Path:
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("FORMAL_VERIFIER", "local")
    monkeypatch.setenv("STORY_MAKER_BASE_URL", f"http://127.0.0.1:{_free_port()}")
    monkeypatch.delenv("CI", raising=False)
    return isolated_root


def _db_path(base_env: Path) -> Path:
    return base_env / "backend" / "data" / "story-maker.db"


def _init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = make_engine(db_path)
    create_schema(engine)
    engine.dispose()


# --- 020-C01: los cinco briefs del repositorio son válidos ----------------------------------


def test_the_five_eval_briefs_are_schema_brief_valid_with_no_c1_to_c6_contradiction() -> None:
    """020-C01: exactamente cinco briefs, todos válidos; el adversarial lleva una instrucción
    dirigida al sistema en un texto libre, y el temporal un recuerdo con una partida definitiva
    (`excluded`) que un deseo de trama contradice."""
    files = sorted(EVAL_BRIEFS_DIR.glob("*.json"))

    assert len(files) == 5
    by_slug: dict[str, tuple[BriefContent, list[str]]] = {}
    slugs = []
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        slugs.append(data["name"])
        content, banned_entries, free_texts = _eval_brief_content(data)
        problems = brief_problems(
            content, CREATED_AT, banned_entries, [], EVAL_MAX_MANDATORY_ELEMENTS
        )
        assert problems == [], (path.name, problems)
        by_slug[data["name"]] = (content, free_texts)

    assert slugs == list(EVAL_BRIEF_SLUGS)

    _adversarial_content, adversarial_free_texts = by_slug["adversarial"]
    assert any("instrucciones" in text.lower() for text in adversarial_free_texts)

    temporal_content, _temporal_free_texts = by_slug["temporal"]
    excluded_names = {r.excluded for r in temporal_content.recollections if r.excluded}
    assert excluded_names
    assert any(
        excluded in wish.statement
        for excluded in excluded_names
        for wish in temporal_content.plot_wishes
    )


# --- 020-C02: sin un cliente registrado no se crea nada -------------------------------------


def test_evals_run_without_email_creates_nothing(base_env: Path) -> None:
    result = runner.invoke(app, ["evals", "run"])

    assert result.exit_code != 0
    assert result.stdout.strip() != ""


def test_evals_run_with_an_unregistered_email_creates_nothing(base_env: Path) -> None:
    db_path = _db_path(base_env)
    _init_db(db_path)

    result = runner.invoke(app, ["evals", "run", "--email", "nadie@example.com"])

    assert result.exit_code != 0
    assert "nadie@example.com" in result.stdout
    engine = make_engine(db_path)
    try:
        with make_session_factory(engine)() as session:
            assert session.query(models.Novel).count() == 0
            assert session.query(models.Brief).count() == 0
            assert session.query(models.Run).count() == 0
    finally:
        engine.dispose()


# --- 020-C05: `evals run` no corre en la CI ---------------------------------------------------


def test_evals_run_refuses_to_run_in_ci(base_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = _db_path(base_env)
    _init_db(db_path)
    user_email = "cliente@example.com"
    engine = make_engine(db_path)
    try:
        with make_session_factory(engine)() as session:
            session.add(models.User(email=user_email, password_hash="h", created_at=NOW))
            session.commit()
    finally:
        engine.dispose()
    monkeypatch.setenv("CI", "true")

    result = runner.invoke(app, ["evals", "run", "--email", user_email])

    assert result.exit_code != 0
    engine = make_engine(db_path)
    try:
        with make_session_factory(engine)() as session:
            assert session.query(models.Novel).count() == 0
    finally:
        engine.dispose()

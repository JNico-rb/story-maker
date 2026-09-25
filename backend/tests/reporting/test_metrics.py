"""`story-maker report metrics` (030): agrega `role_sessions` y `validator_results` en un
Markdown determinista, sin red ni texto de capítulos, prompts, briefs o detalle de validador."""

from __future__ import annotations

import datetime as dt
import itertools
import socket
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.orm import Session
from typer.testing import CliRunner

import story_maker.settings as settings_module
from story_maker.cli import app
from story_maker.store import models
from story_maker.store.session import make_engine, make_session_factory

NOW = dt.datetime(2026, 9, 24, 11, 0)
runner = CliRunner()
_email_counter = itertools.count()


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
    return isolated_root


@pytest.fixture
def db_path(base_env: Path) -> Path:
    result = runner.invoke(app, ["init-db"])
    assert result.exit_code == 0
    return base_env / "backend" / "data" / "story-maker.db"


def _open_session(db_path: Path) -> tuple[Session, Any]:
    engine = make_engine(db_path)
    return make_session_factory(engine)(), engine


def _add_novel(session: Session) -> int:
    user = models.User(
        email=f"user-{next(_email_counter)}@example.com", password_hash="h", created_at=NOW
    )
    session.add(user)
    session.flush()
    novel = models.Novel(user_id=user.id, title=None, embedding_model="m1", created_at=NOW)
    session.add(novel)
    session.flush()
    return novel.id


def _add_run(session: Session, novel_id: int, **overrides: Any) -> int:
    defaults: dict[str, Any] = {
        "type": "generation",
        "status": "published",
        "phase": None,
        "chapter": None,
        "base_version_id": None,
        "candidate_version_id": None,
        "resumes": 0,
        "reason": None,
        "reason_detail": None,
        "created_at": NOW,
        "finished_at": NOW,
    }
    defaults.update(overrides)
    run = models.Run(novel_id=novel_id, **defaults)
    session.add(run)
    session.flush()
    return run.id


def _add_version(session: Session, novel_id: int) -> int:
    version = models.Version(
        novel_id=novel_id,
        status="candidate",
        number=None,
        base_version_id=None,
        changed_chapters=[],
        pdf_path=None,
        created_at=NOW,
        published_at=None,
    )
    session.add(version)
    session.flush()
    return version.id


def _add_role_session(session: Session, novel_id: int, **overrides: Any) -> int:
    defaults: dict[str, Any] = {
        "run_id": None,
        "role": "writer",
        "chapter": None,
        "model": "claude",
        "prompt_version": "v1",
        "reserved_tokens": 1000,
        "input_tokens": 100,
        "output_tokens": 50,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "cost_usd": 0.01,
        "sdk_cost_usd": 0.01,
        "latency_ms": 100,
        "outcome": "completed",
        "trace_id": None,
    }
    defaults.update(overrides)
    row = models.RoleSession(novel_id=novel_id, **defaults)
    session.add(row)
    session.flush()
    return row.id


def _add_validator_result(session: Session, run_id: int, version_id: int, **overrides: Any) -> int:
    defaults: dict[str, Any] = {
        "validator": "chapter_rubric",
        "chapter": None,
        "passed": True,
        "score": None,
        "detail": {},
        "created_at": NOW,
    }
    defaults.update(overrides)
    row = models.ValidatorResult(run_id=run_id, version_id=version_id, **defaults)
    session.add(row)
    session.flush()
    return row.id


def _section(text: str, heading: str) -> str:
    lines = text.splitlines()
    start = lines.index(heading)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "\n".join(lines[start:end])


def _write_report() -> str:
    result = runner.invoke(app, ["report", "metrics"])
    assert result.exit_code == 0
    return (settings_module.ROOT / "docs" / "metrics.md").read_text(encoding="utf-8")


# --- 030-C07: sin ejecuciones, el informe lo dice ----------------------------------------------


def test_with_no_sessions_or_results_the_report_says_there_are_none(db_path: Path) -> None:
    result = runner.invoke(app, ["report", "metrics"])

    assert result.exit_code == 0
    out = settings_module.ROOT / "docs" / "metrics.md"
    lines = out.read_text(encoding="utf-8").strip("\n").splitlines()
    assert len(lines) == 1
    assert "no hay ejecuciones" in lines[0].lower()


# --- 030-C08: ruta de salida --------------------------------------------------------------------


def test_out_option_writes_to_the_given_path_instead_of_the_default(
    db_path: Path, tmp_path: Path
) -> None:
    custom = tmp_path / "informes" / "custom.md"

    result = runner.invoke(app, ["report", "metrics", "--out", str(custom)])

    assert result.exit_code == 0
    assert custom.is_file()
    assert not (settings_module.ROOT / "docs" / "metrics.md").exists()


def test_without_out_it_writes_to_docs_metrics_md(db_path: Path) -> None:
    result = runner.invoke(app, ["report", "metrics"])

    assert result.exit_code == 0
    assert (settings_module.ROOT / "docs" / "metrics.md").is_file()


def test_out_option_replaces_an_existing_file_entirely(db_path: Path, tmp_path: Path) -> None:
    custom = tmp_path / "metrics.md"
    custom.write_text("contenido viejo que debe desaparecer entero\n" * 5, encoding="utf-8")

    result = runner.invoke(app, ["report", "metrics", "--out", str(custom)])

    assert result.exit_code == 0
    assert "contenido viejo" not in custom.read_text(encoding="utf-8")


# --- 030-C01: coste, tokens y latencia por novela -----------------------------------------------


def test_novel_totals_sum_tokens_cost_and_latency_and_count_runs(db_path: Path) -> None:
    session, engine = _open_session(db_path)
    try:
        novel_a = _add_novel(session)
        novel_b = _add_novel(session)
        run1 = _add_run(session, novel_a)
        run2 = _add_run(session, novel_a)
        run3 = _add_run(session, novel_b)
        _add_role_session(
            session,
            novel_a,
            run_id=run1,
            input_tokens=100,
            output_tokens=50,
            cache_read_tokens=10,
            cache_write_tokens=5,
            cost_usd=1.0,
            latency_ms=200,
        )
        _add_role_session(
            session,
            novel_a,
            run_id=run2,
            input_tokens=200,
            output_tokens=80,
            cache_read_tokens=20,
            cache_write_tokens=15,
            cost_usd=2.0,
            latency_ms=300,
        )
        _add_role_session(  # entrevista fuera de una ejecución: cuenta en su novela, no en runs
            session,
            novel_a,
            run_id=None,
            role="interviewer",
            input_tokens=30,
            output_tokens=10,
            cache_read_tokens=0,
            cache_write_tokens=0,
            cost_usd=0.5,
            latency_ms=50,
        )
        _add_role_session(
            session,
            novel_b,
            run_id=run3,
            input_tokens=10,
            output_tokens=5,
            cache_read_tokens=0,
            cache_write_tokens=0,
            cost_usd=0.1,
            latency_ms=20,
        )
        session.commit()
    finally:
        session.close()
        engine.dispose()

    section = _section(_write_report(), "## Por novela")

    assert f"| {novel_a} | 2 | 330 | 140 | 30 | 20 | 3.5000 | 550 |" in section
    assert f"| {novel_b} | 1 | 10 | 5 | 0 | 0 | 0.1000 | 20 |" in section


# --- 030-C02: por capítulo -----------------------------------------------------------------------


def test_sessions_with_a_chapter_are_grouped_by_novel_and_chapter(db_path: Path) -> None:
    session, engine = _open_session(db_path)
    try:
        novel_id = _add_novel(session)
        run_id = _add_run(session, novel_id)
        _add_role_session(
            session,
            novel_id,
            run_id=run_id,
            role="writer",
            chapter=1,
            input_tokens=100,
            output_tokens=40,
            cache_read_tokens=0,
            cache_write_tokens=0,
            cost_usd=1.0,
            latency_ms=100,
        )
        _add_role_session(
            session,
            novel_id,
            run_id=run_id,
            role="editor",
            chapter=1,
            input_tokens=50,
            output_tokens=10,
            cache_read_tokens=0,
            cache_write_tokens=0,
            cost_usd=0.5,
            latency_ms=50,
        )
        _add_role_session(
            session,
            novel_id,
            run_id=run_id,
            role="writer",
            chapter=2,
            input_tokens=200,
            output_tokens=80,
            cache_read_tokens=0,
            cache_write_tokens=0,
            cost_usd=2.0,
            latency_ms=200,
        )
        _add_role_session(  # sin capítulo (plan): fuera de esta sección
            session,
            novel_id,
            run_id=run_id,
            role="planner",
            chapter=None,
            input_tokens=999,
            output_tokens=999,
            cache_read_tokens=0,
            cache_write_tokens=0,
            cost_usd=9.0,
            latency_ms=900,
        )
        session.commit()
    finally:
        session.close()
        engine.dispose()

    section = _section(_write_report(), "## Por capítulo")

    assert f"| {novel_id} | 1 | 150 | 50 | 0 | 0 | 1.5000 | 150 |" in section
    assert f"| {novel_id} | 2 | 200 | 80 | 0 | 0 | 2.0000 | 200 |" in section
    assert "999" not in section


# --- 030-C03: por rol -----------------------------------------------------------------------------


def test_role_rows_are_ordered_by_cost_descending_with_the_top_spender_first(
    db_path: Path,
) -> None:
    session, engine = _open_session(db_path)
    try:
        novel_id = _add_novel(session)
        run_id = _add_run(session, novel_id)
        _add_role_session(
            session, novel_id, run_id=run_id, role="writer", cost_usd=1.5, latency_ms=10
        )
        _add_role_session(
            session, novel_id, run_id=run_id, role="writer", cost_usd=1.5, latency_ms=10
        )
        _add_role_session(
            session, novel_id, run_id=run_id, role="editor", cost_usd=1.0, latency_ms=10
        )
        _add_role_session(
            session, novel_id, run_id=run_id, role="judge", cost_usd=6.0, latency_ms=10
        )
        session.commit()
    finally:
        session.close()
        engine.dispose()

    section = _section(_write_report(), "## Por rol")
    rows = [line for line in section.splitlines() if line.startswith("| ")][1:]

    assert rows[0].startswith("| judge | 1 |")
    assert "60.0%" in rows[0]
    assert rows[1].startswith("| writer | 2 |")
    assert "30.0%" in rows[1]
    assert rows[2].startswith("| editor | 1 |")
    assert "10.0%" in rows[2]


# --- 030-C04: scores por validador y novela ------------------------------------------------------


def test_validator_results_are_grouped_by_novel_and_validator_with_pass_count_and_score_stats(
    db_path: Path,
) -> None:
    session, engine = _open_session(db_path)
    try:
        novel_a = _add_novel(session)
        novel_b = _add_novel(session)
        run_a = _add_run(session, novel_a)
        run_b = _add_run(session, novel_b)
        version_a = _add_version(session, novel_a)
        version_b = _add_version(session, novel_b)
        _add_validator_result(
            session, run_a, version_a, validator="chapter_rubric", passed=True, score=0.9
        )
        _add_validator_result(
            session, run_a, version_a, validator="chapter_rubric", passed=False, score=0.4
        )
        _add_validator_result(session, run_a, version_a, validator="lean", passed=True, score=None)
        _add_validator_result(
            session, run_b, version_b, validator="chapter_rubric", passed=True, score=0.7
        )
        session.commit()
    finally:
        session.close()
        engine.dispose()

    section = _section(_write_report(), "## Scores por validador y novela")

    assert f"| {novel_a} | chapter_rubric | 2 | 1 | 0.6500 | 0.4000 | 0.9000 |" in section
    assert f"| {novel_a} | lean | 1 | 1 | hueco | hueco | hueco |" in section
    assert f"| {novel_b} | chapter_rubric | 1 | 1 | 0.7000 | 0.7000 | 0.7000 |" in section


# --- 030-C05: versiones de prompt -----------------------------------------------------------


def test_a_run_with_two_prompt_versions_of_the_same_role_shows_both(db_path: Path) -> None:
    session, engine = _open_session(db_path)
    try:
        novel_id = _add_novel(session)
        run_id = _add_run(session, novel_id)
        _add_role_session(session, novel_id, run_id=run_id, role="writer", prompt_version="v1")
        _add_role_session(session, novel_id, run_id=run_id, role="writer", prompt_version="v2")
        _add_role_session(session, novel_id, run_id=run_id, role="editor", prompt_version="v1")
        session.commit()
    finally:
        session.close()
        engine.dispose()

    section = _section(_write_report(), "## Versiones de prompt")

    assert f"| {run_id} | writer | v1, v2 |" in section
    assert f"| {run_id} | editor | v1 |" in section


# --- 030-C06: un dato que falta es un hueco, nunca una estimación -----------------------------


def test_a_session_missing_cost_or_prompt_version_shows_hueco_without_zeroing_the_row(
    db_path: Path,
) -> None:
    session, engine = _open_session(db_path)
    try:
        novel_a = _add_novel(session)
        novel_b = _add_novel(session)
        run_a = _add_run(session, novel_a)
        run_b = _add_run(session, novel_b)
        _add_role_session(  # a novel_a le falta el coste y la versión de prompt
            session,
            novel_a,
            run_id=run_a,
            role="writer",
            prompt_version=None,
            cost_usd=None,
            input_tokens=100,
            output_tokens=50,
            latency_ms=100,
        )
        _add_role_session(  # novel_b va completa: no le afecta el hueco de la otra novela
            session,
            novel_b,
            run_id=run_b,
            role="writer",
            prompt_version="v1",
            cost_usd=2.0,
            input_tokens=20,
            output_tokens=10,
            latency_ms=30,
        )
        session.commit()
    finally:
        session.close()
        engine.dispose()

    text = _write_report()
    novela_section = _section(text, "## Por novela")
    rol_section = _section(text, "## Por rol")
    prompt_section = _section(text, "## Versiones de prompt")

    assert f"| {novel_a} | 1 | 100 | 50 | 0 | 0 | hueco | 100 |" in novela_section
    assert f"| {novel_b} | 1 | 20 | 10 | 0 | 0 | 2.0000 | 30 |" in novela_section
    assert "| writer | 2 | 120 | 60 | 0 | 0 | hueco |" in rol_section
    assert f"| {run_a} | writer | hueco |" in prompt_section


# --- 030-I1: el informe es determinista ---------------------------------------------------------


def test_the_same_database_produces_the_same_report_byte_for_byte(db_path: Path) -> None:
    session, engine = _open_session(db_path)
    try:
        novel_a = _add_novel(session)
        novel_b = _add_novel(session)
        run_a = _add_run(session, novel_a)
        run_b = _add_run(session, novel_b)
        version_a = _add_version(session, novel_a)
        _add_role_session(session, novel_a, run_id=run_a, role="writer", chapter=1)
        _add_role_session(session, novel_a, run_id=run_a, role="editor", chapter=1)
        _add_role_session(session, novel_b, run_id=run_b, role="writer", chapter=2)
        _add_validator_result(session, run_a, version_a, validator="chapter_rubric", score=0.5)
        session.commit()
    finally:
        session.close()
        engine.dispose()

    first = _write_report()
    second = _write_report()

    assert first == second
    assert "2026-09" not in first  # sin fecha de generación (I1)


# --- 030-I2: ninguna prueba ni la orden llaman a un modelo, a Langfuse ni a la red -------------


def test_reporting_module_never_imports_the_agent_or_observability_adapters() -> None:
    import inspect

    from story_maker.reporting import metrics as metrics_module

    source = inspect.getsource(metrics_module)
    assert "story_maker.agents" not in source
    assert "story_maker.observability" not in source
    assert "langfuse" not in source.lower()


def test_report_metrics_runs_with_the_network_guard_active_and_no_mock_needed(
    db_path: Path,
) -> None:
    # `tests/conftest.py` bloquea ya toda conexión saliente salvo 127.0.0.1/localhost (001-I3);
    # si `report metrics` intentase red o un modelo, esta orden fallaría con esa misma prueba.
    result = runner.invoke(app, ["report", "metrics"])

    assert result.exit_code == 0


# --- 030-I3: sin texto de capítulos, prompts, briefs ni detalle JSON de un validador -----------


def test_the_report_never_reproduces_chapter_text_or_a_validators_json_detail(
    db_path: Path,
) -> None:
    session, engine = _open_session(db_path)
    try:
        novel_id = _add_novel(session)
        run_id = _add_run(session, novel_id)
        version_id = _add_version(session, novel_id)
        _add_role_session(session, novel_id, run_id=run_id, role="writer", chapter=1)
        _add_validator_result(
            session,
            run_id,
            version_id,
            validator="chapter_rubric",
            detail={"nota": "SECRETO-DETALLE-JSON-DEL-VALIDADOR-0102030"},
        )
        chapter = models.Chapter(
            version_id=version_id,
            number=1,
            title="SECRETO-TITULO-DE-CAPITULO",
            text="SECRETO-TEXTO-DE-CAPITULO",
            summary="SECRETO-RESUMEN-DE-CAPITULO",
            word_count=2,
            content_hash="abc123",
        )
        session.add(chapter)
        session.commit()
    finally:
        session.close()
        engine.dispose()

    text = _write_report()

    assert "SECRETO" not in text

"""`init-db`, `check-env` y `serve` (001-C06, C07, C14, C15, C16) e invariantes I1, I2.

004-C01, C02, I2, C03, C04, C05, I3, C06: selección de adaptador de observabilidad y `auth_check`
en `check-env`/`serve`, con el cliente de Langfuse simulado de `tests/conftest.py`."""

from __future__ import annotations

import asyncio
import json
import socket
import threading
import time
from pathlib import Path

import httpx
import pytest
from tests.conftest import FakeLangfuseClient
from typer.testing import CliRunner

import story_maker.cli as cli_module
import story_maker.settings as settings_module
from story_maker.cli import _build_server, _diagnostics, _run_server, app
from story_maker.observability.langfuse_adapter import LangfuseObservability
from story_maker.observability.null import NullObservability
from story_maker.observability.roles import ROLE_LABELS
from story_maker.settings import Settings

REAL_ROOT = settings_module.ROOT
REAL_CONFIG = json.loads((REAL_ROOT / "config.json").read_text(encoding="utf-8"))

runner = CliRunner()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture
def isolated_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Una raíz de proyecto sin `.env` (I8) con su propio `config.json` válido."""
    monkeypatch.setattr(settings_module, "ROOT", tmp_path)
    (tmp_path / "config.json").write_text(json.dumps(REAL_CONFIG), encoding="utf-8")
    return tmp_path


@pytest.fixture
def base_env(monkeypatch: pytest.MonkeyPatch, isolated_root: Path) -> Path:
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("FORMAL_VERIFIER", "local")
    monkeypatch.setenv("STORY_MAKER_BASE_URL", f"http://127.0.0.1:{_free_port()}")
    return isolated_root


# --- C6: init-db crea la base con el esquema completo --------------------------------------------


def test_init_db_creates_the_directory_and_the_database_file(base_env: Path) -> None:
    result = runner.invoke(app, ["init-db"])

    db_path = base_env / "backend" / "data" / "story-maker.db"
    assert result.exit_code == 0
    assert result.stdout.strip() == str(db_path)
    assert db_path.is_file()


# --- C7: init-db no pisa una base existente sin --reset -------------------------------------------


def test_init_db_without_reset_leaves_an_existing_database_untouched(base_env: Path) -> None:
    runner.invoke(app, ["init-db"])
    db_path = base_env / "backend" / "data" / "story-maker.db"
    footprint_before = db_path.stat().st_mtime_ns

    result = runner.invoke(app, ["init-db"])

    assert result.exit_code == 1
    assert "--reset" in result.stdout
    assert str(db_path) in result.stdout
    assert db_path.stat().st_mtime_ns == footprint_before


def test_init_db_reset_recreates_an_empty_database(base_env: Path) -> None:
    runner.invoke(app, ["init-db"])
    db_path = base_env / "backend" / "data" / "story-maker.db"

    import datetime as dt

    from sqlalchemy import text

    from story_maker.store.models import User
    from story_maker.store.session import make_engine, make_session_factory

    engine = make_engine(db_path)
    session = make_session_factory(engine)()
    session.add(User(email="a@b.com", password_hash="h", created_at=dt.datetime(2026, 1, 1)))
    session.commit()
    session.close()
    engine.dispose()

    result = runner.invoke(app, ["init-db", "--reset"])

    assert result.exit_code == 0
    engine = make_engine(db_path)
    with engine.connect() as conn:
        (count,) = conn.execute(text("SELECT count(*) FROM users")).fetchone()
    engine.dispose()
    assert count == 0


# --- C14: check-env informa de cada comprobación --------------------------------------------------


def test_check_env_reports_the_four_checks_ok_with_the_null_double(base_env: Path) -> None:
    runner.invoke(app, ["init-db"])

    result = runner.invoke(app, ["check-env"])

    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 4
    assert "ajustes: ok" in lines[0]
    assert "config: ok" in lines[1]
    assert "base de datos: ok" in lines[2]
    assert "doble nulo" in lines[3]
    assert "sin Langfuse" in lines[3]


def test_check_env_names_a_short_jwt_secret_without_its_value(
    monkeypatch: pytest.MonkeyPatch, isolated_root: Path
) -> None:
    secret = "y" * 31
    monkeypatch.setenv("JWT_SECRET", secret)
    monkeypatch.setenv("FORMAL_VERIFIER", "local")
    monkeypatch.setenv("STORY_MAKER_BASE_URL", f"http://127.0.0.1:{_free_port()}")

    result = runner.invoke(app, ["check-env"])

    assert result.exit_code == 1
    assert "JWT_SECRET" in result.stdout
    assert secret not in result.stdout


def test_check_env_names_a_config_key_above_the_maximum(base_env: Path) -> None:
    bad_config = json.loads((base_env / "config.json").read_text(encoding="utf-8"))
    bad_config["operation"]["token_ceiling"] = 150000
    (base_env / "config.json").write_text(json.dumps(bad_config), encoding="utf-8")

    result = runner.invoke(app, ["check-env"])

    assert result.exit_code == 1
    assert "token_ceiling" in result.stdout


def test_check_env_without_a_database_names_the_path_and_init_db(base_env: Path) -> None:
    result = runner.invoke(app, ["check-env"])

    assert result.exit_code == 1
    assert "init-db" in result.stdout


def test_check_env_with_a_missing_table_or_column_asks_for_init_db_reset(base_env: Path) -> None:
    runner.invoke(app, ["init-db"])
    db_path = base_env / "backend" / "data" / "story-maker.db"

    from sqlalchemy import text

    from story_maker.store.session import make_engine

    engine = make_engine(db_path)
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users DROP COLUMN password_hash"))
    engine.dispose()

    result = runner.invoke(app, ["check-env"])

    assert result.exit_code == 1
    assert "password_hash" in result.stdout
    assert "--reset" in result.stdout


def test_check_env_reports_several_failures_at_once(
    monkeypatch: pytest.MonkeyPatch, isolated_root: Path
) -> None:
    monkeypatch.setenv("JWT_SECRET", "short")
    monkeypatch.setenv("FORMAL_VERIFIER", "local")
    bad_config = json.loads((isolated_root / "config.json").read_text(encoding="utf-8"))
    bad_config["operation"]["token_ceiling"] = 150000
    (isolated_root / "config.json").write_text(json.dumps(bad_config), encoding="utf-8")

    result = runner.invoke(app, ["check-env"])

    assert result.exit_code == 1
    assert "JWT_SECRET" in result.stdout
    assert "token_ceiling" in result.stdout
    assert "init-db" in result.stdout


# --- I1: ningún secreto se reproduce en una salida de fallo -----------------------------------


@pytest.mark.parametrize(
    "var", ["JWT_SECRET", "GITHUB_TOKEN", "LANGFUSE_SECRET_KEY", "LANGFUSE_PUBLIC_KEY"]
)
def test_no_output_reproduces_a_secret_value(
    monkeypatch: pytest.MonkeyPatch, isolated_root: Path, var: str
) -> None:
    marker = "MARCADOR-SECRETO-0102030405"
    monkeypatch.setenv("JWT_SECRET", marker if var == "JWT_SECRET" else "x" * 32)
    monkeypatch.setenv("FORMAL_VERIFIER", "local")
    monkeypatch.setenv(var, marker)

    result = runner.invoke(app, ["check-env"])

    assert marker not in result.stdout


# --- I2: init-db, check-env y serve solo tocan el directorio de datos -------------------------


def test_init_db_and_check_env_only_change_files_inside_the_data_directory(base_env: Path) -> None:
    data_dir = base_env / "backend" / "data"
    ignored = {data_dir, *data_dir.parents} - {base_env.parent}

    def snapshot() -> set[str]:
        return {
            str(p.relative_to(base_env))
            for p in base_env.rglob("*")
            if p not in ignored and not p.is_relative_to(data_dir)
        }

    before = snapshot()
    runner.invoke(app, ["init-db"])
    runner.invoke(app, ["check-env"])
    after = snapshot()

    assert before == after


# --- C15: serve no arranca con config, ajustes o base inválidos -------------------------------


def test_serve_refuses_to_start_with_an_invalid_jwt_secret(
    monkeypatch: pytest.MonkeyPatch, isolated_root: Path
) -> None:
    monkeypatch.setenv("JWT_SECRET", "short")
    monkeypatch.setenv("FORMAL_VERIFIER", "local")

    result = runner.invoke(app, ["serve"])

    assert result.exit_code == 1
    assert "JWT_SECRET" in result.stdout


def test_serve_refuses_to_start_without_a_database(base_env: Path) -> None:
    result = runner.invoke(app, ["serve"])

    assert result.exit_code == 1
    assert "init-db" in result.stdout


# --- C16: serve escucha en STORY_MAKER_BASE_URL, en un solo proceso ---------------------------


def test_serve_rejects_the_reload_option_without_starting(base_env: Path) -> None:
    runner.invoke(app, ["init-db"])

    result = runner.invoke(app, ["serve", "--reload"])

    assert result.exit_code != 0


def test_serve_rejects_the_workers_option_without_starting(base_env: Path) -> None:
    runner.invoke(app, ["init-db"])

    result = runner.invoke(app, ["serve", "--workers", "2"])

    assert result.exit_code != 0


def test_serve_listens_on_the_configured_host_and_port_and_flushes_once_on_stop(
    base_env: Path,
) -> None:
    runner.invoke(app, ["init-db"])
    from story_maker.settings import load_settings

    settings = load_settings()
    observability = NullObservability()
    server = _build_server(settings, observability)

    def run() -> None:
        asyncio.run(_run_server(server, observability))

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 5
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.05)
        response = httpx.get(f"{settings.base_url}/health", timeout=5)
        assert response.status_code == 200
    finally:
        server.should_exit = True
        thread.join(timeout=5)

    assert observability.flush_count == 1


# --- 004: selección de adaptador, auth_check y prompts vigentes en check-env/serve ------------

LANGFUSE_ENV = {
    "LANGFUSE_PUBLIC_KEY": "pk-marcador-prueba",
    "LANGFUSE_SECRET_KEY": "sk-marcador-prueba",
    "LANGFUSE_BASE_URL": "http://127.0.0.1:9999",
    "LANGFUSE_PROMPT_LABEL": "produccion",
}


def _set_langfuse_env(
    monkeypatch: pytest.MonkeyPatch, overrides: dict[str, str] | None = None
) -> None:
    values = {**LANGFUSE_ENV, **(overrides or {})}
    for key, value in values.items():
        monkeypatch.setenv(key, value)


def _register_all_role_prompts(client: FakeLangfuseClient, label: str = "produccion") -> None:
    for role_label in ROLE_LABELS.values():
        client.register_prompt(role_label, label, version=1)


def _use_fake_langfuse_client(monkeypatch: pytest.MonkeyPatch, client: FakeLangfuseClient) -> None:
    monkeypatch.setattr(cli_module, "build_langfuse_client", lambda settings: client)


# --- C01: con las cuatro variables de Langfuse, se usa el adaptador real ----------------------


def test_check_env_with_the_four_langfuse_vars_uses_the_real_adapter_to_export(
    monkeypatch: pytest.MonkeyPatch, base_env: Path, fake_langfuse_client: FakeLangfuseClient
) -> None:
    runner.invoke(app, ["init-db"])
    _set_langfuse_env(monkeypatch)
    _register_all_role_prompts(fake_langfuse_client)
    _use_fake_langfuse_client(monkeypatch, fake_langfuse_client)

    lines, observability = _diagnostics()

    observability_line = next(line for line in lines if line.startswith("observabilidad"))
    assert "doble nulo" not in observability_line
    assert isinstance(observability, LangfuseObservability)

    with observability.trace("run:1", name="generacion"):
        pass
    observability.flush()

    assert fake_langfuse_client.roots  # lo emitido llegó al cliente simulado, no al doble nulo


# --- C02: sin alguna variable de Langfuse, se usa el doble nulo -------------------------------


def test_check_env_without_the_prompt_label_uses_the_null_double(
    monkeypatch: pytest.MonkeyPatch, base_env: Path, fake_langfuse_client: FakeLangfuseClient
) -> None:
    runner.invoke(app, ["init-db"])
    _set_langfuse_env(monkeypatch)
    monkeypatch.delenv("LANGFUSE_PROMPT_LABEL", raising=False)
    _use_fake_langfuse_client(monkeypatch, fake_langfuse_client)

    lines, observability = _diagnostics()

    observability_line = next(line for line in lines if line.startswith("observabilidad"))
    assert "doble nulo" in observability_line
    assert "sin Langfuse" in observability_line
    assert isinstance(observability, NullObservability)
    assert not fake_langfuse_client.roots
    assert not fake_langfuse_client.scores


# --- I2: con alguna variable ausente, el puerto usa siempre el doble nulo ---------------------


@pytest.mark.parametrize(
    "present",
    [
        (),
        ("LANGFUSE_PROMPT_LABEL",),
        ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL"),
    ],
    ids=["ninguna", "una", "tres"],
)
def test_with_zero_one_or_three_of_the_four_vars_the_port_is_always_the_null_double(
    monkeypatch: pytest.MonkeyPatch,
    base_env: Path,
    fake_langfuse_client: FakeLangfuseClient,
    present: tuple[str, ...],
) -> None:
    runner.invoke(app, ["init-db"])
    for key in LANGFUSE_ENV:
        monkeypatch.delenv(key, raising=False)
    for key in present:
        monkeypatch.setenv(key, LANGFUSE_ENV[key])

    def _build_client_that_must_not_be_called(settings: Settings) -> FakeLangfuseClient:
        raise AssertionError("con alguna variable ausente nunca se construye el cliente real")

    monkeypatch.setattr(cli_module, "build_langfuse_client", _build_client_that_must_not_be_called)

    lines, observability = _diagnostics()

    assert isinstance(observability, NullObservability)
    observability_line = next(line for line in lines if line.startswith("observabilidad"))
    assert "doble nulo" in observability_line


# --- C03: check-env informa «ok» con credenciales válidas y prompts vigentes ------------------


def test_check_env_reports_ok_for_langfuse_with_valid_credentials_and_prompts(
    monkeypatch: pytest.MonkeyPatch, base_env: Path, fake_langfuse_client: FakeLangfuseClient
) -> None:
    runner.invoke(app, ["init-db"])
    _set_langfuse_env(monkeypatch)
    _register_all_role_prompts(fake_langfuse_client)
    _use_fake_langfuse_client(monkeypatch, fake_langfuse_client)

    result = runner.invoke(app, ["check-env"])

    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert lines[3] == "observabilidad: ok (Langfuse)"


# --- C04: check-env falla si las credenciales de Langfuse no son válidas -----------------------


def test_check_env_fails_naming_langfuse_when_credentials_are_invalid(
    monkeypatch: pytest.MonkeyPatch, base_env: Path, fake_langfuse_client: FakeLangfuseClient
) -> None:
    runner.invoke(app, ["init-db"])
    _set_langfuse_env(monkeypatch)
    fake_langfuse_client.auth_ok = False
    _use_fake_langfuse_client(monkeypatch, fake_langfuse_client)

    result = runner.invoke(app, ["check-env"])

    assert result.exit_code == 1
    assert "Langfuse" in result.stdout
    assert "credenciales" in result.stdout
    assert LANGFUSE_ENV["LANGFUSE_SECRET_KEY"] not in result.stdout
    assert LANGFUSE_ENV["LANGFUSE_PUBLIC_KEY"] not in result.stdout


# --- C05: check-env falla si a un rol le falta el prompt con la etiqueta vigente ---------------


def test_check_env_fails_naming_the_role_missing_its_current_prompt(
    monkeypatch: pytest.MonkeyPatch, base_env: Path, fake_langfuse_client: FakeLangfuseClient
) -> None:
    runner.invoke(app, ["init-db"])
    _set_langfuse_env(monkeypatch)
    _register_all_role_prompts(fake_langfuse_client)
    del fake_langfuse_client._prompts[("writer", "produccion")]
    _use_fake_langfuse_client(monkeypatch, fake_langfuse_client)

    result = runner.invoke(app, ["check-env"])

    assert result.exit_code == 1
    assert "writer" in result.stdout


# --- I3: auth_check() nunca falla en silencio --------------------------------------------------


def test_check_env_reports_an_unexpected_auth_check_error_instead_of_ok_or_a_crash(
    monkeypatch: pytest.MonkeyPatch, base_env: Path, fake_langfuse_client: FakeLangfuseClient
) -> None:
    runner.invoke(app, ["init-db"])
    _set_langfuse_env(monkeypatch)
    fake_langfuse_client.auth_raises = RuntimeError("langfuse cloud unreachable")
    _use_fake_langfuse_client(monkeypatch, fake_langfuse_client)

    result = runner.invoke(app, ["check-env"])

    assert result.exit_code == 1
    assert "observabilidad: ok" not in result.stdout
    assert "Langfuse" in result.stdout


# --- C06: serve no arranca en las mismas situaciones que check-env -----------------------------


def test_serve_refuses_to_start_with_invalid_langfuse_credentials(
    monkeypatch: pytest.MonkeyPatch, base_env: Path, fake_langfuse_client: FakeLangfuseClient
) -> None:
    runner.invoke(app, ["init-db"])
    _set_langfuse_env(monkeypatch)
    fake_langfuse_client.auth_ok = False
    _use_fake_langfuse_client(monkeypatch, fake_langfuse_client)

    result = runner.invoke(app, ["serve"])

    assert result.exit_code == 1
    assert "Langfuse" in result.stdout


def test_serve_refuses_to_start_when_a_role_is_missing_its_current_prompt(
    monkeypatch: pytest.MonkeyPatch, base_env: Path, fake_langfuse_client: FakeLangfuseClient
) -> None:
    runner.invoke(app, ["init-db"])
    _set_langfuse_env(monkeypatch)
    _register_all_role_prompts(fake_langfuse_client)
    del fake_langfuse_client._prompts[("juez", "produccion")]
    _use_fake_langfuse_client(monkeypatch, fake_langfuse_client)

    result = runner.invoke(app, ["serve"])

    assert result.exit_code == 1
    assert "judge" in result.stdout

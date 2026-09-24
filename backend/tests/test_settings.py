"""Ajustes del servidor: valores por defecto, rutas desde la raíz, precedencia del entorno (001-C03)."""

from pathlib import Path

import pytest

from story_maker.settings import ROOT, load_settings

BASE_ENV = {"JWT_SECRET": "x" * 32, "FORMAL_VERIFIER": "local"}


def test_defaults_resolve_relative_to_the_repo_root() -> None:
    settings = load_settings(env=BASE_ENV, env_file=Path("no-existe.env"))

    assert settings.data_dir == ROOT / "backend" / "data"
    assert settings.config_path == ROOT / "config.json"
    assert settings.base_url == "http://127.0.0.1:8000"
    assert settings.frontend_dist == ROOT / "frontend" / "dist"
    assert settings.llm_provider == "claude_login"


def test_a_relative_data_dir_resolves_from_the_repo_root() -> None:
    settings = load_settings(
        env={**BASE_ENV, "STORY_MAKER_DATA_DIR": "tmp/datos"}, env_file=Path("no-existe.env")
    )

    assert settings.data_dir == ROOT / "tmp" / "datos"


def test_an_absolute_path_is_used_as_is(tmp_path: Path) -> None:
    settings = load_settings(
        env={**BASE_ENV, "STORY_MAKER_CONFIG": str(tmp_path / "c.json")},
        env_file=Path("no-existe.env"),
    )

    assert settings.config_path == tmp_path / "c.json"


def test_a_present_but_empty_variable_counts_as_absent() -> None:
    settings = load_settings(
        env={**BASE_ENV, "STORY_MAKER_CONFIG": ""}, env_file=Path("no-existe.env")
    )

    assert settings.config_path == ROOT / "config.json"


def test_the_environment_prevails_over_the_dotenv_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(f"JWT_SECRET={'a' * 32}\n", encoding="utf-8")

    settings = load_settings(env={**BASE_ENV, "JWT_SECRET": "b" * 32}, env_file=env_file)

    assert settings.jwt_secret == "b" * 32


def test_without_a_dotenv_file_only_environment_variables_are_read() -> None:
    settings = load_settings(env=BASE_ENV, env_file=Path("no-existe.env"))

    assert settings.jwt_secret == "x" * 32


def test_a_dotenv_variable_is_used_when_the_environment_lacks_it(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(f"JWT_SECRET={'a' * 32}\nFORMAL_VERIFIER=local\n", encoding="utf-8")

    settings = load_settings(env={}, env_file=env_file)

    assert settings.jwt_secret == "a" * 32


@pytest.mark.parametrize("cwd", [ROOT, ROOT / "backend"])
def test_the_current_directory_never_changes_the_result(
    monkeypatch: pytest.MonkeyPatch, cwd: Path
) -> None:
    monkeypatch.chdir(cwd)

    settings = load_settings(env=BASE_ENV, env_file=Path("no-existe.env"))

    assert settings.data_dir == ROOT / "backend" / "data"

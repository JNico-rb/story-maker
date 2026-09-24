"""Ajustes del servidor: valores por defecto, rutas y precedencia del entorno (001-C03, 001-C04)."""

from pathlib import Path

import pytest

from story_maker.settings import ROOT, SettingsError, load_settings

BASE_ENV = {"JWT_SECRET": "x" * 32, "FORMAL_VERIFIER": "local"}


def _errors(env: dict[str, str]) -> list[str]:
    with pytest.raises(SettingsError) as excinfo:
        load_settings(env=env, env_file=Path("no-existe.env"))
    return excinfo.value.errors


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


def test_missing_jwt_secret_is_rejected_naming_it() -> None:
    errors = _errors({"FORMAL_VERIFIER": "local"})

    assert any("JWT_SECRET" in e for e in errors)


def test_a_jwt_secret_of_31_characters_is_rejected_without_showing_the_value() -> None:
    secret = "y" * 31
    errors = _errors({"JWT_SECRET": secret, "FORMAL_VERIFIER": "local"})

    assert any("JWT_SECRET" in e and "32" in e for e in errors)
    assert not any(secret in e for e in errors)


def test_a_jwt_secret_of_32_characters_is_valid() -> None:
    settings = load_settings(env=BASE_ENV, env_file=Path("no-existe.env"))

    assert settings.jwt_secret == "x" * 32


def test_missing_formal_verifier_is_rejected_without_a_default() -> None:
    errors = _errors({"JWT_SECRET": "x" * 32})

    assert any("FORMAL_VERIFIER" in e for e in errors)


def test_an_unknown_formal_verifier_is_rejected_naming_the_admitted_values() -> None:
    errors = _errors({**BASE_ENV, "FORMAL_VERIFIER": "remote"})

    assert any("local" in e and "github" in e for e in errors)


def test_formal_verifier_github_without_its_three_variables_names_each_missing_one() -> None:
    errors = _errors({**BASE_ENV, "FORMAL_VERIFIER": "github"})

    joined = "; ".join(errors)
    assert "GITHUB_REPOSITORY" in joined
    assert "LEAN_WORKFLOW" in joined
    assert "GITHUB_TOKEN" in joined


def test_formal_verifier_github_with_the_three_variables_is_valid() -> None:
    settings = load_settings(
        env={
            **BASE_ENV,
            "FORMAL_VERIFIER": "github",
            "GITHUB_REPOSITORY": "owner/repo",
            "LEAN_WORKFLOW": "lean-verify.yml",
            "GITHUB_TOKEN": "t" * 20,
        },
        env_file=Path("no-existe.env"),
    )

    assert settings.formal_verifier == "github"


def test_formal_verifier_local_without_the_three_variables_is_valid() -> None:
    settings = load_settings(env=BASE_ENV, env_file=Path("no-existe.env"))

    assert settings.formal_verifier == "local"


def test_an_unknown_llm_provider_is_rejected_naming_the_admitted_values() -> None:
    errors = _errors({**BASE_ENV, "LLM_PROVIDER": "openai"})

    assert any("claude_login" in e and "anthropic_compatible" in e for e in errors)


def test_anthropic_compatible_without_any_credentials_names_the_two_forms() -> None:
    errors = _errors({**BASE_ENV, "LLM_PROVIDER": "anthropic_compatible"})

    assert any("ANTHROPIC_BASE_URL" in e and "OPENROUTER_API_KEY" in e for e in errors)


def test_anthropic_compatible_with_anthropic_base_url_and_token_is_valid() -> None:
    settings = load_settings(
        env={
            **BASE_ENV,
            "LLM_PROVIDER": "anthropic_compatible",
            "ANTHROPIC_BASE_URL": "https://api.anthropic.com",
            "ANTHROPIC_AUTH_TOKEN": "t" * 20,
        },
        env_file=Path("no-existe.env"),
    )

    assert settings.llm_provider == "anthropic_compatible"


def test_anthropic_compatible_with_only_openrouter_api_key_is_valid() -> None:
    settings = load_settings(
        env={**BASE_ENV, "LLM_PROVIDER": "anthropic_compatible", "OPENROUTER_API_KEY": "k" * 20},
        env_file=Path("no-existe.env"),
    )

    assert settings.llm_provider == "anthropic_compatible"


def test_claude_login_or_no_provider_is_valid_without_provider_credentials() -> None:
    settings_default = load_settings(env=BASE_ENV, env_file=Path("no-existe.env"))
    settings_explicit = load_settings(
        env={**BASE_ENV, "LLM_PROVIDER": "claude_login"}, env_file=Path("no-existe.env")
    )

    assert settings_default.llm_provider == "claude_login"
    assert settings_explicit.llm_provider == "claude_login"


@pytest.mark.parametrize("base_url", ["ftp://x", "http://127.0.0.1"])
def test_a_base_url_without_scheme_host_and_port_is_rejected(base_url: str) -> None:
    errors = _errors({**BASE_ENV, "STORY_MAKER_BASE_URL": base_url})

    assert any("STORY_MAKER_BASE_URL" in e for e in errors)


def test_without_any_langfuse_variable_settings_are_valid() -> None:
    settings = load_settings(env=BASE_ENV, env_file=Path("no-existe.env"))

    assert settings.langfuse_public_key is None
    assert settings.langfuse_secret_key is None
    assert settings.langfuse_base_url is None

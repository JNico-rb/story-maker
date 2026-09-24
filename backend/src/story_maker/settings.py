"""Ajustes del servidor: entorno y `.env` de la raíz (`definitions.md` §11.3, `arch.md` §15.5)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

# settings.py está en backend/src/story_maker/; la raíz del repo es cuatro niveles arriba.
# Basarse en la ruta del fichero, no en el directorio actual: eso hace C3 independiente del cwd.
ROOT = Path(__file__).resolve().parents[3]

_BASE_URL_RE = re.compile(r"^http://[^/\s]+:\d+$")


class SettingsError(ValueError):
    """Ajustes inválidos; `errors` nombra cada clave, sin reproducir ningún valor secreto."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    config_path: Path
    base_url: str
    frontend_dist: Path
    jwt_secret: str
    llm_provider: str
    formal_verifier: str
    github_repository: str | None
    lean_workflow: str | None
    github_token: str | None
    claude_code_oauth_token: str | None
    anthropic_base_url: str | None
    anthropic_auth_token: str | None
    openrouter_api_key: str | None
    langfuse_public_key: str | None
    langfuse_secret_key: str | None
    langfuse_base_url: str | None
    langfuse_prompt_label: str | None


def _read_dotenv(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    result: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip().strip('"')
    return result


def _resolve_path(value: str | None, default: Path) -> Path:
    if not value:
        return default
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_settings(env: dict[str, str] | None = None, env_file: Path | None = None) -> Settings:
    """Lee ajustes de `env` (por defecto `os.environ`) y del `.env` raíz; el entorno prevalece."""
    source_env = dict(os.environ if env is None else env)
    dotenv = _read_dotenv(env_file if env_file is not None else ROOT / ".env")

    def get(key: str) -> str | None:
        return source_env.get(key) or dotenv.get(key) or None

    errors: list[str] = []

    data_dir = _resolve_path(get("STORY_MAKER_DATA_DIR"), ROOT / "backend" / "data")
    config_path = _resolve_path(get("STORY_MAKER_CONFIG"), ROOT / "config.json")
    frontend_dist = _resolve_path(get("STORY_MAKER_FRONTEND_DIST"), ROOT / "frontend" / "dist")

    base_url = get("STORY_MAKER_BASE_URL") or "http://127.0.0.1:8000"
    if not _BASE_URL_RE.fullmatch(base_url):
        errors.append(
            f"STORY_MAKER_BASE_URL debe tener la forma http://host:puerto (recibido: '{base_url}')"
        )

    jwt_secret = get("JWT_SECRET")
    if not jwt_secret:
        errors.append("JWT_SECRET es obligatorio")
    elif len(jwt_secret) < 32:
        errors.append("JWT_SECRET debe tener 32 caracteres o más")

    formal_verifier = get("FORMAL_VERIFIER")
    if formal_verifier not in ("local", "github"):
        errors.append("FORMAL_VERIFIER es obligatorio: 'local' o 'github'")
    elif formal_verifier == "github":
        for key in ("GITHUB_REPOSITORY", "LEAN_WORKFLOW", "GITHUB_TOKEN"):
            if not get(key):
                errors.append(f"{key} es obligatorio con FORMAL_VERIFIER=github")

    llm_provider = get("LLM_PROVIDER") or "claude_login"
    if llm_provider not in ("claude_login", "anthropic_compatible"):
        errors.append("LLM_PROVIDER debe ser 'claude_login' o 'anthropic_compatible'")
    elif llm_provider == "anthropic_compatible":
        has_anthropic = bool(get("ANTHROPIC_BASE_URL") and get("ANTHROPIC_AUTH_TOKEN"))
        has_openrouter = bool(get("OPENROUTER_API_KEY"))
        if not has_anthropic and not has_openrouter:
            errors.append(
                "LLM_PROVIDER=anthropic_compatible exige ANTHROPIC_BASE_URL y "
                "ANTHROPIC_AUTH_TOKEN, u OPENROUTER_API_KEY"
            )

    if errors:
        raise SettingsError(errors)

    return Settings(
        data_dir=data_dir,
        config_path=config_path,
        base_url=base_url,
        frontend_dist=frontend_dist,
        jwt_secret=cast(str, jwt_secret),
        llm_provider=llm_provider,
        formal_verifier=cast(str, formal_verifier),
        github_repository=get("GITHUB_REPOSITORY"),
        lean_workflow=get("LEAN_WORKFLOW"),
        github_token=get("GITHUB_TOKEN"),
        claude_code_oauth_token=get("CLAUDE_CODE_OAUTH_TOKEN"),
        anthropic_base_url=get("ANTHROPIC_BASE_URL"),
        anthropic_auth_token=get("ANTHROPIC_AUTH_TOKEN"),
        openrouter_api_key=get("OPENROUTER_API_KEY"),
        langfuse_public_key=get("LANGFUSE_PUBLIC_KEY"),
        langfuse_secret_key=get("LANGFUSE_SECRET_KEY"),
        langfuse_base_url=get("LANGFUSE_BASE_URL"),
        langfuse_prompt_label=get("LANGFUSE_PROMPT_LABEL"),
    )

"""`.env.example` lista los ajustes sin valores, sin más y sin menos (001-C05)."""

from __future__ import annotations

import re

from story_maker.settings import ROOT

EXPECTED = {
    "STORY_MAKER_DATA_DIR",
    "STORY_MAKER_CONFIG",
    "STORY_MAKER_BASE_URL",
    "STORY_MAKER_FRONTEND_DIST",
    "JWT_SECRET",
    "LLM_PROVIDER",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_AUTH_TOKEN",
    "OPENROUTER_API_KEY",
    "FORMAL_VERIFIER",
    "GITHUB_REPOSITORY",
    "LEAN_WORKFLOW",
    "GITHUB_TOKEN",
    "LANGFUSE_PROMPT_LABEL",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_BASE_URL",
}

ENV_EXAMPLE = ROOT / ".env.example"


def _assignments() -> list[tuple[str, str]]:
    pairs = []
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = re.match(r"^([A-Z_][A-Z0-9_]*)=(.*)$", stripped)
        assert match, f"línea no reconocida: {line}"
        pairs.append((match.group(1), match.group(2)))
    return pairs


def test_each_expected_variable_appears_exactly_once() -> None:
    names = [name for name, _ in _assignments()]

    assert set(names) == EXPECTED
    assert len(names) == len(EXPECTED)


def test_every_variable_is_left_empty() -> None:
    for name, value in _assignments():
        assert value == "", f"{name} no debería llevar valor"


def test_langfuse_mcp_auth_is_only_mentioned_in_a_comment() -> None:
    text = ENV_EXAMPLE.read_text(encoding="utf-8")

    assert "LANGFUSE_MCP_AUTH" in text
    assignments = [name for name, _ in _assignments()]
    assert "LANGFUSE_MCP_AUTH" not in assignments


def test_copied_to_env_with_only_jwt_secret_and_formal_verifier_local_settings_are_valid(
    tmp_path,
) -> None:
    from story_maker.settings import load_settings

    env_file = tmp_path / ".env"
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    text = text.replace("JWT_SECRET=", f"JWT_SECRET={'x' * 32}", 1)
    text = text.replace("FORMAL_VERIFIER=", "FORMAL_VERIFIER=local", 1)
    env_file.write_text(text, encoding="utf-8")

    settings = load_settings(env={}, env_file=env_file)

    assert settings.jwt_secret == "x" * 32
    assert settings.formal_verifier == "local"

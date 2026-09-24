"""Configuración que el puerto construye para el SDK: perfil, aislamiento, proveedor (003-C01..C07).

Lo observable en T es esta configuración (`verification.md` §4.7); que el SDK la respeta lo
demuestran 003-C30 a 003-C32 (D)."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

import pytest
from claude_agent_sdk import ClaudeAgentOptions
from pydantic import BaseModel, Field

from story_maker.agents.port import SessionRequest
from story_maker.agents.profiles import role_profile
from story_maker.agents.sdk import ProviderConfigError, SdkAgent
from story_maker.agents.tools import ToolSpec
from story_maker.config import Config
from story_maker.settings import Settings


class NoHooks:
    """Los hooks no corren al construir la configuración."""

    def before_tool(self, call_id: str, tool: str, tool_input: dict[str, Any]) -> str | None:
        raise AssertionError

    def run_tool(self, tool: str, tool_input: dict[str, Any]) -> tuple[str, bool]:
        raise AssertionError

    def after_tool(self, call_id: str, tool: str) -> str | None:
        raise AssertionError


@pytest.fixture
def build_options(
    config: Config,
    workspace: Path,
    make_settings: Callable[..., Settings],
    make_request: Callable[..., SessionRequest],
) -> Callable[..., ClaudeAgentOptions]:
    def build(role: str, mode: str | None = None, **settings: Any) -> ClaudeAgentOptions:
        agent = SdkAgent(make_settings(**settings), workspace=workspace)
        request = make_request(role, mode)
        return agent.session_options(request, role_profile(config, role, mode), NoHooks())

    return build


def exposed_tools(options: ClaudeAgentOptions) -> set[str]:
    """Integradas activas más las preaprobadas, con el nombre sin prefijo MCP."""
    builtin = set(options.tools) if isinstance(options.tools, list) else {"<preset>"}
    return builtin | {name.rsplit("__", 1)[-1] for name in options.allowed_tools}


@pytest.mark.parametrize(
    ("role", "mode", "expected"),
    [
        ("interviewer", None, {"update_brief"}),
        ("extractor", None, {"submit_facts"}),
        ("planner", "plan", {"submit_plan"}),
        ("planner", "change", {"propose_change"}),
        ("writer", "write", {"submit_chapter", "Skill"}),
        ("writer", "rewrite", {"submit_chapter", "Skill"}),
        ("writer", "revise", {"submit_chapter", "Skill"}),
        ("editor", None, {"submit_review", "Skill"}),
        ("judge", None, {"submit_evaluation"}),
        (
            "visual_reviewer",
            None,
            {"submit_visual_review", "browser_navigate", "browser_snapshot", "browser_click"},
        ),
    ],
)
def test_each_role_opens_with_its_whitelist_and_nothing_else(
    role: str,
    mode: str | None,
    expected: set[str],
    config: Config,
    build_options: Callable[..., ClaudeAgentOptions],
) -> None:
    options = build_options(role, mode)

    assert exposed_tools(options) == expected
    # ninguna integrada del CLI salvo Skill; lo no preaprobado se deniega sin preguntar
    assert set(options.tools or []) <= {"Skill"}
    assert options.permission_mode == "dontAsk"
    assert options.model == config.roles[role].model
    assert options.max_turns == config.roles[role].max_turns


@pytest.mark.parametrize(("role", "mode"), [("interviewer", None), ("writer", "write")])
def test_the_session_runs_isolated_in_the_workspace(
    role: str,
    mode: str | None,
    tmp_path: Path,
    config: Config,
    make_settings: Callable[..., Settings],
    make_request: Callable[..., SessionRequest],
) -> None:
    outer = tmp_path / "repo"
    inner = outer / "backend"
    workspace = inner / "harness_workspace"
    personal = tmp_path / "home" / ".claude"
    for directory in (workspace, personal):
        directory.mkdir(parents=True)
    for directory in (outer, inner, workspace, personal):
        (directory / "CLAUDE.md").write_text(f"instrucciones de {directory.name}", encoding="utf-8")
    agent = SdkAgent(make_settings(), workspace=workspace, user_claude_dir=personal)

    options = agent.session_options(
        make_request(role, mode), role_profile(config, role, mode), NoHooks()
    )

    assert Path(str(options.cwd)) == workspace
    assert options.setting_sources == ["project"]
    excluded = json.loads(str(options.settings))["claudeMdExcludes"]
    for directory in (outer, inner, personal):
        assert (directory / "CLAUDE.md").resolve().as_posix() in excluded
    assert (workspace / "CLAUDE.md").resolve().as_posix() not in excluded
    assert options.strict_mcp_config is True
    assert set(options.mcp_servers) == {"harness"}
    assert options.permission_mode == "dontAsk"
    assert options.continue_conversation is False
    assert options.resume is None
    assert options.session_id is None
    assert options.env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] == "1"
    assert options.env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] == "1"


def external_servers(options: ClaudeAgentOptions) -> dict[str, Any]:
    assert isinstance(options.mcp_servers, dict)
    return {
        name: server for name, server in options.mcp_servers.items() if server.get("type") != "sdk"
    }


def test_only_the_visual_reviewer_declares_the_browser_mcp(
    config: Config,
    make_settings: Callable[..., Settings],
    build_options: Callable[..., ClaudeAgentOptions],
) -> None:
    data_dir = make_settings().data_dir
    reviewer = build_options("visual_reviewer")

    (browser,) = external_servers(reviewer).values()
    args = browser["args"]
    assert "@playwright/mcp@0.0.82" in args
    assert args[args.index("--browser") + 1] == "msedge"
    output = Path(args[args.index("--output-dir") + 1])
    assert output.is_relative_to(data_dir)
    browser_tools = {t for t in reviewer.allowed_tools if not t.startswith("mcp__harness__")}
    assert browser_tools == {
        "mcp__playwright__browser_navigate",
        "mcp__playwright__browser_snapshot",
        "mcp__playwright__browser_click",
    }
    for role, mode in [
        ("interviewer", None),
        ("extractor", None),
        ("planner", "plan"),
        ("planner", "change"),
        ("writer", "write"),
        ("editor", None),
        ("judge", None),
    ]:
        assert external_servers(build_options(role, mode)) == {}


CREDENTIALS = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "OPENROUTER_API_KEY",
)


def session_env(options: ClaudeAgentOptions) -> dict[str, str]:
    """El entorno del subproceso: el del servidor más `options.env`, como lo mezcla el SDK."""
    return {**os.environ, **options.env}


def credentials_in(env: dict[str, str]) -> dict[str, str]:
    return {key: env[key] for key in CREDENTIALS if env.get(key)}


@pytest.fixture
def clean_environ(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    for key in (*CREDENTIALS, "CLAUDE_CONFIG_DIR"):
        monkeypatch.delenv(key, raising=False)
    return monkeypatch


def assert_login_basics(options: ClaudeAgentOptions) -> None:
    assert "CLAUDE_CONFIG_DIR" not in options.env
    assert "CLAUDE_CONFIG_DIR" not in session_env(options)
    assert options.env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] == "1"
    assert options.env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] == "1"


def test_with_claude_login_and_no_token_the_session_carries_no_credential(
    clean_environ: pytest.MonkeyPatch, build_options: Callable[..., ClaudeAgentOptions]
) -> None:
    options = build_options("interviewer")

    assert_login_basics(options)
    assert credentials_in(session_env(options)) == {}


def test_with_claude_login_and_a_token_the_session_carries_only_that_token(
    clean_environ: pytest.MonkeyPatch, build_options: Callable[..., ClaudeAgentOptions]
) -> None:
    options = build_options("interviewer", claude_code_oauth_token="TU_TOKEN_OAUTH_AQUI")

    assert_login_basics(options)
    assert credentials_in(session_env(options)) == {
        "CLAUDE_CODE_OAUTH_TOKEN": "TU_TOKEN_OAUTH_AQUI"
    }


def test_with_claude_login_inherited_anthropic_variables_reach_the_session_empty(
    clean_environ: pytest.MonkeyPatch, build_options: Callable[..., ClaudeAgentOptions]
) -> None:
    clean_environ.setenv("ANTHROPIC_API_KEY", "TU_CLAVE_AQUI")
    clean_environ.setenv("ANTHROPIC_AUTH_TOKEN", "TU_TOKEN_AQUI")
    clean_environ.setenv("ANTHROPIC_BASE_URL", "http://127.0.0.1:9/proxy-de-prueba")

    options = build_options("interviewer", openrouter_api_key="TU_CLAVE_OPENROUTER_AQUI")

    assert_login_basics(options)
    env = session_env(options)
    assert credentials_in(env) == {}
    assert "TU_CLAVE_OPENROUTER_AQUI" not in env.values()


BASE = "http://127.0.0.1:9/endpoint-de-prueba"


@pytest.mark.parametrize(
    ("settings", "expected"),
    [
        (
            {"anthropic_base_url": BASE, "anthropic_auth_token": "TU_TOKEN_AQUI"},
            {"ANTHROPIC_BASE_URL": BASE, "ANTHROPIC_AUTH_TOKEN": "TU_TOKEN_AQUI"},
        ),
        (
            {"openrouter_api_key": "TU_CLAVE_OPENROUTER_AQUI"},
            {
                "ANTHROPIC_BASE_URL": "https://openrouter.ai/api",
                "ANTHROPIC_AUTH_TOKEN": "TU_CLAVE_OPENROUTER_AQUI",
            },
        ),
        (
            {
                "anthropic_base_url": BASE,
                "anthropic_auth_token": "TU_TOKEN_AQUI",
                "openrouter_api_key": "TU_CLAVE_OPENROUTER_AQUI",
            },
            {"ANTHROPIC_BASE_URL": BASE, "ANTHROPIC_AUTH_TOKEN": "TU_TOKEN_AQUI"},
        ),
    ],
)
def test_with_anthropic_compatible_the_session_carries_only_its_endpoint_variables(
    settings: dict[str, str],
    expected: dict[str, str],
    clean_environ: pytest.MonkeyPatch,
    build_options: Callable[..., ClaudeAgentOptions],
) -> None:
    clean_environ.setenv("ANTHROPIC_API_KEY", "TU_CLAVE_AQUI")
    clean_environ.setenv("CLAUDE_CODE_OAUTH_TOKEN", "TU_TOKEN_OAUTH_AQUI")

    options = build_options(
        "interviewer",
        llm_provider="anthropic_compatible",
        claude_code_oauth_token="TU_TOKEN_OAUTH_AQUI",
        **settings,
    )

    assert_login_basics(options)
    env = session_env(options)
    assert credentials_in(env) == expected
    assert env["ANTHROPIC_API_KEY"] == ""


@pytest.mark.parametrize(
    ("settings", "named"),
    [
        ({}, ["ANTHROPIC_AUTH_TOKEN", "OPENROUTER_API_KEY"]),
        ({"anthropic_base_url": BASE}, ["ANTHROPIC_AUTH_TOKEN", "OPENROUTER_API_KEY"]),
        ({"anthropic_auth_token": "TU_TOKEN_AQUI"}, ["ANTHROPIC_BASE_URL"]),
        (
            {"anthropic_auth_token": "TU_TOKEN_AQUI", "openrouter_api_key": "TU_CLAVE_AQUI"},
            ["ANTHROPIC_BASE_URL"],
        ),
    ],
)
def test_anthropic_compatible_without_its_variables_does_not_build_the_adapter(
    settings: dict[str, str],
    named: list[str],
    workspace: Path,
    make_settings: Callable[..., Settings],
) -> None:
    with pytest.raises(ProviderConfigError) as failed:
        SdkAgent(
            make_settings(llm_provider="anthropic_compatible", **settings), workspace=workspace
        )

    for variable in named:
        assert variable in str(failed.value)


class PlanInput(BaseModel):
    title: str
    dedication: str | None = None
    tone: Literal["tender", "funny", "epic"]
    beats: list[str] = Field(min_length=2, max_length=4)


def harness_server(options: ClaudeAgentOptions) -> Any:
    assert isinstance(options.mcp_servers, dict)
    return options.mcp_servers["harness"]["instance"]  # type: ignore[typeddict-item]


async def test_the_schema_the_session_publishes_is_the_one_derived_from_the_tool_model(
    config: Config,
    workspace: Path,
    make_settings: Callable[..., Settings],
    make_request: Callable[..., SessionRequest],
) -> None:
    tool = ToolSpec(name="submit_plan", model=PlanInput, description="Entrega el plan")
    agent = SdkAgent(make_settings(), workspace=workspace)
    options = agent.session_options(
        make_request("planner", "plan", tools=(tool,)),
        role_profile(config, "planner", "plan"),
        NoHooks(),
    )

    listing = await harness_server(options).get_request_handler("tools/list").handler(None, None)

    (published,) = listing.tools
    assert published.name == "submit_plan"
    schema = published.input_schema
    assert schema == PlanInput.model_json_schema()
    assert sorted(schema["required"]) == ["beats", "title", "tone"]
    assert schema["properties"]["tone"]["enum"] == ["tender", "funny", "epic"]
    assert schema["properties"]["beats"]["minItems"] == 2
    assert schema["properties"]["beats"]["maxItems"] == 4

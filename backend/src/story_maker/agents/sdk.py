"""Adaptador del puerto de agente sobre el Claude Agent SDK (`architecture.md` §7, §15.2)."""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ClaudeSDKError,
    McpSdkServerConfig,
    McpServerConfig,
    ResultError,
    ResultMessage,
)
from claude_agent_sdk.types import McpStdioServerConfig
from mcp.server import Server, ServerRequestContext
from mcp.types import (
    CallToolRequestParams,
    CallToolResult,
    ListToolsResult,
    PaginatedRequestParams,
    TextContent,
    Tool,
)

from story_maker.agents.port import DriverSession, EndingName, Final, SessionRequest, ToolHooks
from story_maker.agents.profiles import BROWSER_TOOLS, SKILL, RoleProfile
from story_maker.agents.tools import ToolSpec
from story_maker.agents.usage import Usage
from story_maker.settings import Settings

HARNESS = "harness"
BROWSER = "playwright"
PLAYWRIGHT_MCP = "@playwright/mcp@0.0.82"
OPENROUTER_BASE_URL = "https://openrouter.ai/api"
# Lo que se espera, tras `interrupt()`, al resultado final con el uso de la sesión.
INTERRUPT_GRACE_SECONDS = 5


# Telemetría no esencial y memoria automática del CLI apagadas (`architecture.md` §12.6).
CLI_SWITCHES = {
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
}


class ProviderConfigError(ValueError):
    """Faltan las variables del endpoint de `anthropic_compatible`."""


class RealModelInTests(RuntimeError):
    """Una prueba intentó abrir una sesión real: las pruebas T usan el doble falso (003-I6)."""


def final_from_result(message: ResultMessage) -> Final:
    """El `ResultMessage` de la sesión: su uso es el exacto, también si agotó los turnos."""
    ending: EndingName
    if message.subtype == "error_max_turns":
        ending = "turns_exhausted"
    elif message.is_error:
        ending = "provider_error"
    else:
        ending = "completed"
    raw = message.usage
    usage = (
        Usage(
            input_tokens=raw.get("input_tokens", 0),
            output_tokens=raw.get("output_tokens", 0),
            cache_read_tokens=raw.get("cache_read_input_tokens", 0),
            cache_write_tokens=raw.get("cache_creation_input_tokens", 0),
        )
        if raw is not None
        else None
    )
    return Final(ending, message.result, usage, message.total_cost_usd)


@dataclass
class SdkSession:
    """Una sesión del CLI: conectar, enviar el mensaje y leer hasta el resultado final."""

    options: ClaudeAgentOptions
    message: str
    final: Final | None = None
    _client: ClaudeSDKClient | None = None

    async def run(self) -> None:
        self._client = ClaudeSDKClient(self.options)
        await self._client.connect()
        await self._client.query(self.message)
        await self._receive(self._client)

    async def _receive(self, client: ClaudeSDKClient) -> None:
        try:
            async for message in client.receive_response():
                if isinstance(message, ResultMessage):
                    self.final = final_from_result(message)
        except ResultError:
            # Agotar max_turns lanza ResultError después del ResultMessage: el uso ya llegó.
            if self.final is None:
                raise

    async def interrupt(self) -> None:
        """`interrupt()` corta, pero el subproceso vive hasta `disconnect()` (§15.2, H9)."""
        if self._client is None:
            return
        client = self._client
        with contextlib.suppress(TimeoutError, ClaudeSDKError):
            await client.interrupt()
            async with asyncio.timeout(INTERRUPT_GRACE_SECONDS):
                await self._receive(client)

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.disconnect()


def harness_tools(tools: Sequence[ToolSpec]) -> list[Tool]:
    """Las tools propias tal como se publican al modelo, con el schema de su modelo Pydantic."""
    return [
        Tool(name=spec.name, description=spec.description, input_schema=spec.schema())
        for spec in tools
    ]


def provider_env(settings: Settings) -> dict[str, str]:
    """Variables de la sesión según `LLM_PROVIDER` (§15.2); nunca redefine `CLAUDE_CONFIG_DIR`."""
    if settings.llm_provider == "anthropic_compatible":
        return CLI_SWITCHES | _endpoint_env(settings) | {"CLAUDE_CODE_OAUTH_TOKEN": ""}
    # Una ANTHROPIC_* heredada del servidor cobraría créditos de API: llega vacía (§18, spec 003).
    env = CLI_SWITCHES | {
        "ANTHROPIC_API_KEY": "",
        "ANTHROPIC_AUTH_TOKEN": "",
        "ANTHROPIC_BASE_URL": "",
    }
    if settings.claude_code_oauth_token:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = settings.claude_code_oauth_token
    return env


def _endpoint_env(settings: Settings) -> dict[str, str]:
    """El endpoint compatible con Anthropic; `ANTHROPIC_API_KEY` siempre vacía (§18, spec 003)."""
    if settings.anthropic_auth_token:
        if not settings.anthropic_base_url:
            raise ProviderConfigError(
                "LLM_PROVIDER=anthropic_compatible: ANTHROPIC_AUTH_TOKEN exige ANTHROPIC_BASE_URL"
            )
        base_url, token = settings.anthropic_base_url, settings.anthropic_auth_token
    elif settings.openrouter_api_key:
        base_url, token = OPENROUTER_BASE_URL, settings.openrouter_api_key
    else:
        raise ProviderConfigError(
            "LLM_PROVIDER=anthropic_compatible exige ANTHROPIC_BASE_URL y ANTHROPIC_AUTH_TOKEN, "
            "u OPENROUTER_API_KEY"
        )
    return {"ANTHROPIC_BASE_URL": base_url, "ANTHROPIC_AUTH_TOKEN": token, "ANTHROPIC_API_KEY": ""}


def claude_md_excludes(workspace: Path, user_claude_dir: Path) -> list[str]:
    """Todos los `CLAUDE.md` que no son el del workspace: los de sus padres y el personal."""
    parents = [directory / "CLAUDE.md" for directory in workspace.resolve().parents]
    return [path.as_posix() for path in [*parents, (user_claude_dir / "CLAUDE.md").resolve()]]


def _harness_server(tools: Sequence[ToolSpec], hooks: ToolHooks) -> McpSdkServerConfig:
    """Servidor MCP en proceso; valida con Pydantic, no con jsonschema: da todos los errores."""
    listed = harness_tools(tools)

    async def on_list_tools(
        ctx: ServerRequestContext[Any, Any], params: PaginatedRequestParams | None
    ) -> ListToolsResult:
        return ListToolsResult(tools=listed)

    async def on_call_tool(
        ctx: ServerRequestContext[Any, Any], params: CallToolRequestParams
    ) -> CallToolResult:
        text, is_error = hooks.run_tool(params.name, dict(params.arguments or {}))
        return CallToolResult(content=[TextContent(type="text", text=text)], is_error=is_error)

    server: Server[Any] = Server(
        HARNESS, version="1", on_list_tools=on_list_tools, on_call_tool=on_call_tool
    )
    return McpSdkServerConfig(type="sdk", name=HARNESS, instance=server)


class SdkAgent:
    def __init__(
        self, settings: Settings, *, workspace: Path, user_claude_dir: Path | None = None
    ) -> None:
        self._settings = settings
        self._workspace = workspace
        self._user_claude_dir = user_claude_dir
        self._env = provider_env(settings)

    def prepare(self, request: SessionRequest) -> None:
        # pytest fija PYTEST_CURRENT_TEST en cada prueba: así ninguna llega al CLI ni al modelo.
        if "PYTEST_CURRENT_TEST" in os.environ:
            raise RealModelInTests(
                f"sesión real de {request.role} en la suite: usa el doble falso del puerto"
            )

    def session_options(
        self, request: SessionRequest, profile: RoleProfile, hooks: ToolHooks
    ) -> ClaudeAgentOptions:
        builtin = [SKILL] if profile.uses_skill else []
        allowed = [f"mcp__{HARNESS}__{spec.name}" for spec in request.tools] + builtin
        servers: dict[str, McpServerConfig] = {HARNESS: _harness_server(request.tools, hooks)}
        if profile.role == "visual_reviewer":
            servers[BROWSER] = self._browser_server()
            allowed += [f"mcp__{BROWSER}__{tool}" for tool in BROWSER_TOOLS]
        user_claude_dir = self._user_claude_dir or Path(
            os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude"
        )
        excludes = claude_md_excludes(self._workspace, user_claude_dir)
        return ClaudeAgentOptions(
            tools=builtin,
            allowed_tools=allowed,
            mcp_servers=servers,
            strict_mcp_config=True,
            permission_mode="dontAsk",
            model=profile.model,
            max_turns=profile.max_turns,
            system_prompt=request.prompt,
            cwd=self._workspace,
            setting_sources=["project"],
            settings=json.dumps({"claudeMdExcludes": excludes}),
            env=dict(self._env),
        )

    def _browser_server(self) -> McpStdioServerConfig:
        """Playwright MCP fijado (§15.1) sobre el Edge instalado, con su salida en los datos."""
        output = self._settings.data_dir / "playwright-mcp"
        return McpStdioServerConfig(
            type="stdio",
            command="cmd",
            args=[
                "/c",
                "npx",
                "-y",
                PLAYWRIGHT_MCP,
                "--browser",
                "msedge",
                "--output-dir",
                str(output),
            ],
        )

    def open(
        self, request: SessionRequest, profile: RoleProfile, hooks: ToolHooks
    ) -> DriverSession:
        return SdkSession(self.session_options(request, profile, hooks), request.message)

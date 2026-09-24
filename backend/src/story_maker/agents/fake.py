"""Doble falso determinista del puerto de agente: sigue un guion por sesión (003-C28, C29).

Llama a los hooks de `LiveSession` en el orden en que lo hace el SDK: `PreToolUse`, manejador de
la tool propia y `PostToolUse`. Sin red, sin CLI y sin `.env`."""

from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

from story_maker.agents.port import Final, SessionRequest, ToolHooks
from story_maker.agents.profiles import RoleProfile
from story_maker.agents.usage import Usage


@dataclass(frozen=True)
class Say:
    """El modelo responde con texto y termina."""

    text: str


@dataclass(frozen=True)
class Call:
    """El modelo llama a una tool con esta entrada."""

    tool: str
    input: dict[str, Any]


Step = Say | Call


@dataclass(frozen=True)
class Script:
    steps: tuple[Step, ...]
    usage: Usage | None = None
    sdk_cost_usd: float | None = None


@dataclass
class FakeSession:
    request: SessionRequest
    profile: RoleProfile
    hooks: ToolHooks
    script: Script
    final: Final | None = None
    reads: list[str] = field(default_factory=list)
    disconnected: bool = False

    async def run(self) -> None:
        text: str | None = None
        for number, step in enumerate(self.script.steps, start=1):
            await asyncio.sleep(0)
            if isinstance(step, Say):
                text = step.text
                break
            self.reads.append(self._call(f"call-{number}", step))
        self.final = Final("completed", text, self.script.usage, self.script.sdk_cost_usd)

    def _call(self, call_id: str, step: Call) -> str:
        """Lo que el modelo lee tras la llamada, como con el SDK."""
        denial = self.hooks.before_tool(call_id, step.tool, step.input)
        if denial is not None:
            return denial
        if step.tool in self.profile.own_tools:
            output, _is_error = self.hooks.run_tool(step.tool, step.input)
            replacement = self.hooks.after_tool(call_id, step.tool)
            return replacement if replacement is not None else output
        self.hooks.after_tool(call_id, step.tool)
        return "Hecho."

    async def disconnect(self) -> None:
        self.disconnected = True


class FakeAgent:
    def __init__(self) -> None:
        self._scripts: dict[tuple[str, str | None], deque[Script]] = defaultdict(deque)
        self.sessions: list[FakeSession] = []

    def script(self, role: str, mode: str | None, script: Script) -> None:
        """Encola el guion de la próxima sesión de ese rol y modo."""
        self._scripts[(role, mode)].append(script)

    def prepare(self, request: SessionRequest) -> None:
        return None

    def open(self, request: SessionRequest, profile: RoleProfile, hooks: ToolHooks) -> FakeSession:
        script = self._scripts[(request.role, request.mode)].popleft()
        session = FakeSession(request, profile, hooks, script)
        self.sessions.append(session)
        return session

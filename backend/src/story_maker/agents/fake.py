"""Doble falso determinista del puerto de agente: sigue un guion por sesión (003-C28, C29).

Llama a los hooks de `LiveSession` en el orden en que lo hace el SDK: `PreToolUse`, manejador de
la tool propia y `PostToolUse`. Sin red, sin CLI y sin `.env`."""

from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

from story_maker.agents.port import EndingName, Final, SessionRequest, ToolHooks
from story_maker.agents.profiles import RoleProfile
from story_maker.agents.usage import Usage


class MissingScript(LookupError):
    """La prueba abrió una sesión de un rol y modo para el que no dio guion."""

    def __init__(self, role: str, mode: str | None) -> None:
        super().__init__(f"sin guion para el rol {role} en modo {mode}")


@dataclass(frozen=True)
class Say:
    """El modelo responde con texto y termina."""

    text: str


@dataclass(frozen=True)
class Call:
    """El modelo llama a una tool con esta entrada."""

    tool: str
    input: dict[str, Any]


@dataclass(frozen=True)
class Hang:
    """La sesión no termina; tras `interrupt()` llega el resultado final si `result`."""

    result: bool = True


@dataclass(frozen=True)
class Fail:
    """Falla el proveedor: con `result`, cierra con un resultado de error; sin él, el transporte."""

    result: bool = False


Step = Say | Call | Hang | Fail


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
    interrupted: bool = False
    disconnected: bool = False
    _hanging: Hang | None = None

    async def run(self) -> None:
        """Cada paso es un turno; pasar de `max_turns` termina la sesión, como en el SDK."""
        text: str | None = None
        for turn, step in enumerate(self.script.steps, start=1):
            await asyncio.sleep(0)
            if self.hooks.stopping:
                return
            if turn > self.profile.max_turns:
                self.final = self._final("turns_exhausted")
                return
            match step:
                case Say():
                    text = step.text
                    break
                case Hang():
                    self._hanging = step
                    await asyncio.Event().wait()
                case Fail(result=True):
                    self.final = self._final("provider_error")
                    return
                case Fail():
                    raise ConnectionError("el transporte del proveedor falló a mitad de sesión")
                case Call():
                    self.reads.append(self._call(f"call-{turn}", step))
        self.final = self._final("completed", text)

    def _final(self, ending: EndingName, text: str | None = None) -> Final:
        return Final(ending, text, self.script.usage, self.script.sdk_cost_usd)

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

    async def interrupt(self) -> None:
        """Como el SDK tras `interrupt()`: llega el resultado final, salvo `Hang(result=False)`."""
        self.interrupted = True
        arrives = self._hanging is None or self._hanging.result
        if self.final is None and arrives:
            self.final = self._final("interrupted")

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
        if not self._scripts[(request.role, request.mode)]:
            raise MissingScript(request.role, request.mode)

    def open(self, request: SessionRequest, profile: RoleProfile, hooks: ToolHooks) -> FakeSession:
        script = self._scripts[(request.role, request.mode)].popleft()
        session = FakeSession(request, profile, hooks, script)
        self.sessions.append(session)
        return session

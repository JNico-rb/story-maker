"""Puerto de agente: la única vía a un modelo (`architecture.md` §7, §15.9 regla 5).

Lo común a los siete roles vive aquí, igual para los dos adaptadores (el del Agent SDK y el
doble falso): perfil del rol, reserva en el techo, hooks de policy, de validación de capítulo y
de observabilidad, validación por schema, límites, registro de la `SesionDeRol` y spans. Cada
adaptador solo conduce la sesión y llama a los hooks de `LiveSession` como lo haría el SDK."""

from __future__ import annotations

import asyncio
import re
import time
from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager, ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import TokenCeiling, reservation
from story_maker.agents.policy_port import PolicyEngine, PolicyField, PolicyRequest
from story_maker.agents.profiles import RoleProfile, role_profile
from story_maker.agents.tools import ToolSpec
from story_maker.agents.usage import Usage, cost_usd
from story_maker.config import Config
from story_maker.observability.port import ModelCall, Score, Span, Trace
from story_maker.store.models import RoleSession
from story_maker.store.session import unit_of_work

Outcome = Literal["completed", "turns_exhausted", "time_exhausted", "cut", "infrastructure_failure"]
CallStatus = Literal["accepted", "schema_rejected", "denied", "blocked"]
EndingName = Literal["completed", "turns_exhausted", "provider_error", "interrupted"]

# Cómo termina la sesión según su resultado final; `interrupted` solo llega tras un corte.
_OUTCOME_OF: dict[EndingName, Outcome] = {
    "completed": "completed",
    "turns_exhausted": "turns_exhausted",
    "provider_error": "infrastructure_failure",
    "interrupted": "cut",
}

ACK = "Entrega recibida."
STOPPED = "La sesión se ha cortado."
SKILL_FILE = ".claude/skills/personalizacion-natural/SKILL.md"


@dataclass(frozen=True)
class Defect:
    validator: str
    message: str
    blocking: bool


ChapterChecks = Callable[[BaseModel], Sequence[Defect]]


@dataclass(frozen=True)
class SessionRequest:
    """Lo que da quien abre la sesión; sin `run_id` es una sesión de la API."""

    role: str
    mode: str | None
    user_id: int
    novel_id: int
    prompt: str
    message: str
    tools: tuple[ToolSpec, ...]
    trace: Trace
    parent_span: Span | None = None
    run_id: int | None = None
    chapter: int | None = None
    prompt_version: str | None = None
    chapter_checks: ChapterChecks | None = None
    cut_when: Callable[[ToolCall], bool] | None = None


@dataclass
class ToolCall:
    tool: str
    input: dict[str, Any]
    status: CallStatus
    value: BaseModel | None = None
    errors: tuple[str, ...] = ()
    reason: str | None = None
    defects: tuple[Defect, ...] = ()
    own: bool = False


@dataclass
class SessionResult:
    outcome: Outcome
    calls: list[ToolCall]
    text: str | None
    model: str
    usage: Usage | None
    cost_usd: float | None
    sdk_cost_usd: float | None
    latency_ms: int
    reserved_tokens: int
    role_session_id: int
    error: BaseException | None = None

    @property
    def deliveries(self) -> list[ToolCall]:
        """Llamadas aceptadas a tools propias, en orden; la última es la que el rol entrega."""
        return [call for call in self.calls if call.own and call.status == "accepted"]


@dataclass
class Final:
    """El resultado final de la sesión (el `ResultMessage` del SDK)."""

    ending: EndingName
    text: str | None
    usage: Usage | None
    sdk_cost_usd: float | None


class ToolHooks(Protocol):
    """Lo que un adaptador llama en cada llamada a tool, en el orden del SDK."""

    def before_tool(self, call_id: str, tool: str, tool_input: dict[str, Any]) -> str | None: ...

    def run_tool(self, tool: str, tool_input: dict[str, Any]) -> tuple[str, bool]: ...

    def after_tool(self, call_id: str, tool: str) -> str | None: ...

    @property
    def stopping(self) -> bool: ...


class DriverSession(Protocol):
    final: Final | None

    async def run(self) -> None: ...

    async def interrupt(self) -> None: ...

    async def disconnect(self) -> None: ...


class Agent(Protocol):
    """Un adaptador del puerto: el del Agent SDK o el doble falso."""

    def prepare(self, request: SessionRequest) -> None: ...

    def open(
        self, request: SessionRequest, profile: RoleProfile, hooks: ToolHooks
    ) -> DriverSession: ...


class Telemetry(Protocol):
    """Lo que el puerto emite por el puerto de observabilidad (doble nulo en las pruebas)."""

    def span(
        self,
        trace: Trace,
        name: str,
        parent: Span | None = None,
        metadata: dict[str, Any] | None = None,
        level: str = "DEFAULT",
        reason: str | None = None,
    ) -> AbstractContextManager[Span]: ...

    def model_call(
        self,
        span: Span,
        *,
        model: str,
        prompt_version: str | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        cost_usd: float = 0.0,
        latency_ms: int = 0,
    ) -> ModelCall: ...

    def score(
        self,
        trace: Trace,
        name: str,
        value: float,
        comment: str | None = None,
        span: Span | None = None,
    ) -> Score: ...


@dataclass
class _Pending:
    """Una llamada que la política dejó pasar y aún no se ha resuelto."""

    tool: str
    input: dict[str, Any]
    span: ExitStack | None = None
    value: BaseModel | None = None
    handled: bool = False


@dataclass
class LiveSession:
    """Los hooks de una sesión abierta; cada sesión tiene los suyos (003-I8)."""

    request: SessionRequest
    profile: RoleProfile
    policy: PolicyEngine
    telemetry: Telemetry
    role_span: Span
    calls: list[ToolCall] = field(default_factory=list)
    stop_outcome: Outcome | None = None
    error: BaseException | None = None
    stopped: asyncio.Event = field(default_factory=asyncio.Event)
    _pending: dict[str, _Pending] = field(default_factory=dict)

    @property
    def stopping(self) -> bool:
        return self.stop_outcome is not None

    def stop(self, outcome: Outcome, error: BaseException | None = None) -> None:
        """Pide al puerto que corte la sesión; desde aquí no corre ninguna tool más."""
        if self.stop_outcome is None:
            self.stop_outcome, self.error = outcome, error
            self.stopped.set()

    @property
    def _specs(self) -> dict[str, ToolSpec]:
        return {spec.name: spec for spec in self.request.tools}

    def before_tool(self, call_id: str, tool: str, tool_input: dict[str, Any]) -> str | None:
        """Hook de policy (`PreToolUse`): None deja correr la tool; un texto la deniega."""
        if self.stopping:
            return STOPPED
        spec = self._specs.get(tool)
        try:
            decision = self.policy.decide(
                PolicyRequest(
                    origin="policy_hook",
                    user_id=self.request.user_id,
                    novel_id=self.request.novel_id,
                    run_id=self.request.run_id,
                    role=self.request.role,
                    tool=tool,
                    fields=_fields(tool_input, spec.narrative if spec else ()),
                )
            )
        except Exception as exc:
            # Sin decisión no corre ninguna tool; no es un intento del rol (§18, spec 003).
            self.stop("infrastructure_failure", exc)
            return STOPPED
        if decision.decision == "deny":
            reason = decision.reason or "denegada por la política"
            with self._tool_span(tool, "WARNING", reason):
                pass
            self._record_call(
                ToolCall(tool, tool_input, "denied", reason=reason, own=tool in self._specs)
            )
            return reason
        pending = _Pending(tool=tool, input=tool_input)
        if tool not in self._specs:
            pending.span = ExitStack()
            pending.span.enter_context(self._tool_span(tool))
        self._pending[call_id] = pending
        return None

    def run_tool(self, tool: str, tool_input: dict[str, Any]) -> tuple[str, bool]:
        """Manejador de una tool propia: valida por schema y entrega en memoria."""
        pending = next(
            p
            for p in self._pending.values()
            if p.tool == tool and p.input == tool_input and not p.handled
        )
        pending.handled = True
        value, errors = self._specs[tool].validate(tool_input)
        if value is None:
            self._resolve_own(ToolCall(tool, tool_input, "schema_rejected", errors=errors))
            return f"Entrada inválida para {tool}: " + "; ".join(errors), True
        if tool == "submit_chapter" and self.request.chapter_checks is not None:
            pending.value = value
        else:
            self._resolve_own(ToolCall(tool, tool_input, "accepted", value=value))
        return ACK, False

    def after_tool(self, call_id: str, tool: str) -> str | None:
        """Hook de validación de capítulo y de observabilidad (`PostToolUse`)."""
        pending = self._pending.pop(call_id, None)
        if pending is None:
            return None
        if pending.span is not None:
            pending.span.close()
            self._record_call(ToolCall(tool, pending.input, "accepted"))
        elif pending.value is not None and self.request.chapter_checks is not None:
            defects = tuple(self.request.chapter_checks(pending.value))
            blocking = tuple(d for d in defects if d.blocking)
            if blocking:
                # PostToolUse no puede bloquear: sustituye lo que lee el modelo (§7.5, H5).
                self._resolve_own(ToolCall(tool, pending.input, "blocked", defects=blocking))
                return _defects_text(blocking)
            call = ToolCall(tool, pending.input, "accepted", value=pending.value, defects=defects)
            self._resolve_own(call)
        return None

    def close(self) -> None:
        for pending in self._pending.values():
            if pending.span is not None:
                pending.span.close()
        self._pending.clear()

    def _tool_span(self, tool: str, level: str = "DEFAULT", reason: str | None = None) -> Any:
        return self.telemetry.span(
            self.request.trace,
            f"tool:{tool}",
            parent=self.role_span,
            level=level,
            reason=reason,
        )

    def _resolve_own(self, call: ToolCall) -> None:
        rejected = call.status == "schema_rejected"
        level = "WARNING" if rejected or call.status == "blocked" else "DEFAULT"
        reason = (
            "; ".join(call.errors)
            if rejected
            else _defects_text(call.defects)
            if call.status == "blocked"
            else None
        )
        with self._tool_span(call.tool, level, reason) as span:
            self.telemetry.score(
                self.request.trace, "schema-salida", 0 if rejected else 1, span=span
            )
        call.own = True
        self._record_call(call)

    def _record_call(self, call: ToolCall) -> None:
        """Quien abrió la sesión ve cada llamada en cuanto se resuelve y puede cortarla."""
        self.calls.append(call)
        if self.request.cut_when is not None and self.request.cut_when(call):
            self.stop("cut")


def _defects_text(defects: Sequence[Defect]) -> str:
    lines = [f"- [{d.validator}] {d.message}" for d in defects]
    return "\n".join(["Defectos bloqueantes:", *lines])


def _fields(tool_input: dict[str, Any], narrative: tuple[str, ...]) -> tuple[PolicyField, ...]:
    """Cada texto de la entrada con su ruta; narrativo si su ruta, sin índices, está marcada.

    La política nunca debe escanear lo no marcado, como una lista de prohibidas (§7.5)."""
    return tuple(
        PolicyField(path=path, value=value, narrative=re.sub(r"\[\d+\]", "[]", path) in narrative)
        for path, value in _texts(tool_input, "")
    )


def _texts(value: Any, path: str) -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, dict):
        return [
            text
            for key, item in value.items()
            for text in _texts(item, f"{path}.{key}" if path else str(key))
        ]
    if isinstance(value, list):
        return [text for i, item in enumerate(value) for text in _texts(item, f"{path}[{i}]")]
    return []


class AgentPort:
    def __init__(
        self,
        *,
        agent: Agent,
        config: Config,
        ceiling: TokenCeiling,
        policy: PolicyEngine,
        telemetry: Telemetry,
        session_factory: sessionmaker[Session],
        workspace: Path,
    ) -> None:
        self._agent = agent
        self._config = config
        self._ceiling = ceiling
        self._policy = policy
        self._telemetry = telemetry
        self._session_factory = session_factory
        self._workspace = workspace

    def reservation(self, request: SessionRequest) -> int:
        """Lo que la sesión reserva en el techo, estimado sobre los textos que envía el código."""
        profile = role_profile(self._config, request.role, request.mode)
        chars = (
            len(request.prompt)
            + self._workspace_chars("CLAUDE.md")
            + (self._workspace_chars(SKILL_FILE) if profile.uses_skill else 0)
            + sum(len(spec.schema_text()) for spec in request.tools)
            + len(request.message)
        )
        return reservation(chars, profile.max_turns, profile.max_output_tokens)

    def _workspace_chars(self, relative: str) -> int:
        path = self._workspace / relative
        return len(path.read_text(encoding="utf-8")) if path.is_file() else 0

    async def run(self, request: SessionRequest) -> SessionResult:
        profile = role_profile(self._config, request.role, request.mode)
        profile.check_tools([spec.name for spec in request.tools])
        self._agent.prepare(request)
        reserved = self.reservation(request)
        # En la API se espera como mucho `api_wait_seconds`; en una ejecución, sin límite propio.
        wait = self._config.api_wait_seconds if request.run_id is None else None
        ticket = await self._ceiling.acquire(reserved, timeout=wait)
        try:
            with self._telemetry.span(
                request.trace,
                f"rol:{profile.label}",
                parent=request.parent_span,
                metadata={"chapter": request.chapter},
            ) as role_span:
                live = LiveSession(request, profile, self._policy, self._telemetry, role_span)
                driver = self._agent.open(request, profile, live)
                started = time.monotonic()
                outcome = await self._drive(driver, live)
                latency_ms = int((time.monotonic() - started) * 1000)
                live.close()
                final = driver.final
                usage = final.usage if final is not None else None
                sdk_cost = final.sdk_cost_usd if final is not None else None
                cost = (
                    cost_usd(usage, self._config.pricing[profile.model])
                    if usage is not None
                    else None
                )
                if usage is not None and cost is not None:
                    self._telemetry.model_call(
                        role_span,
                        model=profile.model,
                        prompt_version=request.prompt_version,
                        input_tokens=usage.input_tokens,
                        output_tokens=usage.output_tokens,
                        cache_read_tokens=usage.cache_read_tokens,
                        cache_write_tokens=usage.cache_write_tokens,
                        cost_usd=cost,
                        latency_ms=latency_ms,
                    )
            row_id = self._record(
                request, profile, outcome, usage, cost, sdk_cost, latency_ms, reserved
            )
        finally:
            self._ceiling.release(ticket)
        return SessionResult(
            outcome=outcome,
            calls=live.calls,
            text=final.text if final is not None else None,
            model=profile.model,
            usage=usage,
            cost_usd=cost,
            sdk_cost_usd=sdk_cost,
            latency_ms=latency_ms,
            reserved_tokens=reserved,
            role_session_id=row_id,
            error=live.error,
        )

    async def _drive(self, driver: DriverSession, live: LiveSession) -> Outcome:
        """Conduce la sesión hasta que termina o un hook pide cortarla; siempre desconecta."""
        running = asyncio.create_task(driver.run())
        stop_requested = asyncio.create_task(live.stopped.wait())
        done, _ = await asyncio.wait(
            {running, stop_requested},
            timeout=self._config.session_timeout_seconds,
            return_when=asyncio.FIRST_COMPLETED,
        )
        stop_requested.cancel()
        if not done:
            live.stop("time_exhausted")
        if live.stop_outcome is not None:
            running.cancel()
            await asyncio.gather(running, return_exceptions=True)
            await driver.interrupt()
            await driver.disconnect()
            return live.stop_outcome
        await driver.disconnect()
        running.result()
        return _OUTCOME_OF[driver.final.ending] if driver.final else "infrastructure_failure"

    def _record(
        self,
        request: SessionRequest,
        profile: RoleProfile,
        outcome: Outcome,
        usage: Usage | None,
        cost: float | None,
        sdk_cost: float | None,
        latency_ms: int,
        reserved: int,
    ) -> int:
        row = RoleSession(
            novel_id=request.novel_id,
            run_id=request.run_id,
            role=request.role,
            chapter=request.chapter,
            model=profile.model,
            prompt_version=request.prompt_version,
            reserved_tokens=reserved,
            input_tokens=usage.input_tokens if usage else None,
            output_tokens=usage.output_tokens if usage else None,
            cache_read_tokens=usage.cache_read_tokens if usage else None,
            cache_write_tokens=usage.cache_write_tokens if usage else None,
            cost_usd=cost,
            sdk_cost_usd=sdk_cost,
            latency_ms=latency_ms,
            outcome=outcome,
            trace_id=request.trace.key,
        )
        with unit_of_work(self._session_factory) as uow:
            uow.add(row)
        return row.id

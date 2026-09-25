"""Una traza `mcp:<tool>` por llamada a una tool, con la máscara de la novela que resolvió
(015-C16, 015-C17, I7, I9, I10).

`request_change` abre su propia traza interna (`propuesta-de-cambio:...`, de 014); para que
cuelgue de `mcp:request_change` en vez de abrir otra (015-C16, «no abre una traza de propuesta
aparte»), se le pasa `ReuseTrace`: un `ObservabilityPort` que ignora la `key` que pida y continúa
siempre la traza ya abierta por la tool. Todo lo demás (spans, scores, prompts) lo delega tal
cual — es lo único distinto de la traza real."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from typing import Any
from uuid import uuid4

from story_maker.observability.mask import Mask
from story_maker.observability.port import ModelCall, ObservabilityPort, Score, Span, Trace


class ReuseTrace:
    """Ve `ObservabilityPort.trace()` como pide 015-C16: cualquier `key` continúa `outer_trace`,
    en vez de abrir una traza nueva."""

    def __init__(self, inner: ObservabilityPort, outer_trace: Trace) -> None:
        self.inner = inner
        self.outer_trace = outer_trace

    @contextmanager
    def trace(
        self, key: str, name: str | None = None, session: str | None = None
    ) -> Iterator[Trace]:
        yield self.outer_trace

    def span(
        self,
        trace: Trace,
        name: str,
        parent: Span | None = None,
        metadata: dict[str, Any] | None = None,
        level: str = "DEFAULT",
        reason: str | None = None,
    ) -> AbstractContextManager[Span]:
        return self.inner.span(
            trace, name, parent=parent, metadata=metadata, level=level, reason=reason
        )

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
        sdk_cost_usd: float | None = None,
    ) -> ModelCall:
        return self.inner.model_call(
            span,
            model=model,
            prompt_version=prompt_version,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            sdk_cost_usd=sdk_cost_usd,
        )

    def score(
        self,
        trace: Trace,
        name: str,
        value: float,
        comment: str | None = None,
        span: Span | None = None,
    ) -> Score:
        return self.inner.score(trace, name, value, comment=comment, span=span)

    def check(self) -> bool:
        return self.inner.check()

    def flush(self) -> None:
        self.inner.flush()

    def get_prompt(self, role: str, label: str) -> str | None:
        return self.inner.get_prompt(role, label)


@contextmanager
def mcp_trace(telemetry: ObservabilityPort, tool: str, session: str | None) -> Iterator[Trace]:
    """Una traza nueva por llamada: la `key` lleva un nonce para que dos llamadas a la misma
    tool no continúen la misma traza (`NullObservability.trace` reutiliza por `key`); su
    `name` es `mcp:<tool>` (015-C16)."""
    name = f"mcp:{tool}"
    with telemetry.trace(f"{name}:{uuid4().hex}", name=name, session=session) as trace:
        yield trace


def record_call(
    telemetry: ObservabilityPort,
    trace: Trace,
    tool: str,
    mask: Mask,
    *,
    input: dict[str, Any] | None = None,
    output: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    """Un span `tool:<tool>` con la entrada y la salida (o el error) enmascaradas (015-C16,
    015-C17). Nivel WARNING si acabó en error, con el motivo."""
    metadata: dict[str, Any] = {}
    if input is not None:
        metadata["input"] = mask.apply_to_value(input)
    if output is not None:
        metadata["output"] = mask.apply_to_value(output)
    level = "DEFAULT" if error is None else "WARNING"
    with telemetry.span(trace, f"tool:{tool}", metadata=metadata, level=level, reason=error):
        pass

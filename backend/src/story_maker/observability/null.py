"""Doble nulo del puerto de observabilidad: captura lo emitido, sin red (001-C19..C21)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from story_maker.observability.port import ModelCall, Score, Span, Trace


class NullObservability:
    """Arranca y opera sin Langfuse; ninguna prueba T exporta (`architecture.md` §13.6)."""

    def __init__(self) -> None:
        self.traces: dict[str, Trace] = {}
        self.flush_count = 0

    @contextmanager
    def trace(
        self, key: str, name: str | None = None, session: str | None = None
    ) -> Iterator[Trace]:
        """La misma `key` continúa la traza existente en lugar de abrir otra (C19)."""
        trace = self.traces.get(key)
        if trace is None:
            trace = Trace(key=key, name=name, session=session)
            self.traces[key] = trace
        yield trace

    @contextmanager
    def span(
        self,
        trace: Trace,
        name: str,
        parent: Span | None = None,
        metadata: dict[str, Any] | None = None,
        level: str = "DEFAULT",
        reason: str | None = None,
    ) -> Iterator[Span]:
        span = Span(name=name, parent=parent, metadata=dict(metadata or {}))
        span.level = level
        span.status_message = reason
        (parent.children if parent is not None else trace.spans).append(span)
        try:
            yield span
        except Exception as exc:
            span.level = "ERROR"
            span.status_message = str(exc)
            raise

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
        call = ModelCall(
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
        span.model_calls.append(call)
        return call

    def score(
        self,
        trace: Trace,
        name: str,
        value: float,
        comment: str | None = None,
        span: Span | None = None,
    ) -> Score:
        result = Score(name=name, value=value, comment=comment, span=span)
        trace.scores.append(result)
        return result

    def get_prompt(self, role: str, label: str) -> str | None:
        return None

    def check(self) -> bool:
        return True

    def flush(self) -> None:
        self.flush_count += 1

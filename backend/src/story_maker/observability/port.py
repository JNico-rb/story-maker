"""Puerto de observabilidad: trazas, spans, llamadas de modelo y scores (`architecture.md` §13)."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ModelCall:
    model: str
    prompt_version: str | None
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    cost_usd: float
    latency_ms: int


@dataclass
class Score:
    name: str
    value: float
    comment: str | None
    span: Span | None


@dataclass
class Span:
    name: str
    parent: Span | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    level: str = "DEFAULT"
    status_message: str | None = None
    model_calls: list[ModelCall] = field(default_factory=list)
    children: list[Span] = field(default_factory=list)


@dataclass
class Trace:
    key: str
    name: str | None = None
    session: str | None = None
    spans: list[Span] = field(default_factory=list)
    scores: list[Score] = field(default_factory=list)


class ObservabilityPort(Protocol):
    """Lo que emite cualquier pieza del harness; `null.NullObservability` es el doble sin red."""

    def trace(
        self, key: str, name: str | None = None, session: str | None = None
    ) -> AbstractContextManager[Trace]: ...

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

    def check(self) -> bool: ...

    def flush(self) -> None: ...

    def get_prompt(self, role: str, label: str) -> str | None: ...

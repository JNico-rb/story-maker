"""Puerto estrecho hacia el SDK de Langfuse v4 que usa el adaptador real (`architecture.md` §13).

Un `langfuse.Langfuse` de verdad lo satisface por estructura; en pruebas lo dobla el cliente
simulado de `tests/conftest.py` (`FakeLangfuseClient`), sin red (004-I2, 004-I7)."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Protocol


class PromptHandlePort(Protocol):
    """Lo que el adaptador lee de un `PromptClient` real: versión y config (huella)."""

    version: int
    config: Any


class ObservationHandlePort(Protocol):
    """Una observación abierta (span o generación); permite anidar y anotar."""

    id: str

    def start_as_current_observation(
        self, *, name: str, as_type: str = "span", **kwargs: Any
    ) -> AbstractContextManager[ObservationHandlePort]: ...


class LangfuseClientPort(Protocol):
    """El subconjunto real de `langfuse.Langfuse` que necesita `LangfuseObservability`."""

    def auth_check(self) -> bool: ...

    def get_prompt(self, name: str, *, label: str) -> PromptHandlePort: ...

    def create_prompt(
        self,
        *,
        name: str,
        prompt: str,
        labels: list[str],
        config: dict[str, Any] | None = None,
    ) -> PromptHandlePort: ...

    def create_trace_id(self, *, seed: str) -> str: ...

    def start_as_current_observation(
        self,
        *,
        trace_context: dict[str, str] | None = None,
        name: str,
        as_type: str = "span",
        **kwargs: Any,
    ) -> AbstractContextManager[ObservationHandlePort]: ...

    def create_score(
        self,
        *,
        name: str,
        value: float,
        comment: str | None = None,
        trace_id: str,
        observation_id: str | None = None,
    ) -> None: ...

    def flush(self) -> None: ...


__all__ = ["LangfuseClientPort", "ObservationHandlePort", "PromptHandlePort"]

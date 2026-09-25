"""Envoltorio común de cada tool: identidad, traza `mcp:<tool>` con la `Sesion` de la novela
propia que resolvió (o ninguna) y su máscara (015-C16, 015-C17, I7, I9, I10)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from sqlalchemy.orm import Session, sessionmaker

from story_maker.api.mcp.masking import mask_for_novel
from story_maker.api.mcp.tracing import mcp_trace, record_call
from story_maker.observability.mask import Mask
from story_maker.observability.port import ObservabilityPort, Trace
from story_maker.store.models import Novel

# Un error de schema nunca llega al cuerpo de la tool (fastmcp valida antes de invocarla), así
# que `traced_tool` no se ejecuta para él. `_tool_entered` es cómo el middleware de transporte
# (`server.py`) distingue ese caso — sigue en `False` — del de una tool que ya abrió y cerró su
# propia traza (015-C16: el error de schema deja igualmente su traza, sin sesión).
_tool_entered: ContextVar[bool] = ContextVar("mcp_tool_entered", default=False)


def tool_was_entered() -> bool:
    return _tool_entered.get()


def novel_id_if_owned(
    session_factory: sessionmaker[Session], novel_id: int | None, user_id: int
) -> int | None:
    if novel_id is None:
        return None
    with session_factory() as session:
        novel = session.get(Novel, novel_id)
        if novel is None or novel.user_id != user_id:
            return None
        return novel.id


def mask_for(session_factory: sessionmaker[Session], novel_id: int | None) -> Mask:
    if novel_id is None:
        return Mask.empty()
    with session_factory() as session:
        return mask_for_novel(session, novel_id)


def mask_union(session_factory: sessionmaker[Session], novel_ids: list[int]) -> Mask:
    """La máscara de una llamada que toca varias novelas: la unión de las de cada una
    (`list_novels`, 015-C17)."""
    mask = Mask.empty()
    with session_factory() as session:
        for novel_id in novel_ids:
            mask = mask | mask_for_novel(session, novel_id)
    return mask


@contextmanager
def traced_tool(
    telemetry: ObservabilityPort,
    session_factory: sessionmaker[Session],
    tool: str,
    *,
    user_id: int,
    novel_id: int | None,
) -> Iterator[tuple[Trace, Mask]]:
    """`novel_id=None` cuando el argumento no resuelve una novela propia (015-C16: sin sesión)."""
    _tool_entered.set(True)
    owned_id = novel_id_if_owned(session_factory, novel_id, user_id)
    mask = mask_for(session_factory, owned_id)
    with mcp_trace(telemetry, tool, str(owned_id) if owned_id is not None else None) as trace:
        yield trace, mask


def as_json(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


class SchemaErrorTracing(Middleware):
    """Un error de schema nunca llega al cuerpo de la tool: fastmcp lo rechaza antes de
    invocarla, así que `traced_tool` no abre su traza. Esta pieza de transporte cubre justo ese
    hueco, sin sesión y sin duplicar la de una tool que sí llegó a ejecutarse (015-C16)."""

    def __init__(self, telemetry: ObservabilityPort) -> None:
        self.telemetry = telemetry

    async def on_call_tool(
        self, context: MiddlewareContext[Any], call_next: CallNext[Any, Any]
    ) -> Any:
        token = _tool_entered.set(False)
        try:
            return await call_next(context)
        except Exception as exc:
            if not _tool_entered.get():
                tool_name = getattr(context.message, "name", "unknown")
                with mcp_trace(self.telemetry, tool_name, None) as trace:
                    record_call(
                        self.telemetry, trace, tool_name, Mask.empty(), input={}, error=str(exc)
                    )
            raise
        finally:
            _tool_entered.reset(token)

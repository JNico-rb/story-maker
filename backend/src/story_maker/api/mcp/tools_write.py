"""Las dos tools de escritura: solo proponen o encolan (015-I2), con la misma interpretación que
la web (`pipeline.changes`, spec 014) y una fila `mcp_write` por llamada (015-I8)."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.port import AgentPort
from story_maker.api.auth import Clock
from story_maker.api.change_requests import PLANNER_CHANGE_PROMPT_FILE
from story_maker.api.errors import field_error
from story_maker.api.interview import MAX_MESSAGE_CHARS
from story_maker.api.mcp.audit import record_mcp_write
from story_maker.api.mcp.errors import from_http_exception
from story_maker.api.mcp.tracing import ReuseTrace
from story_maker.api.ownership import NOT_FOUND_DETAIL, owned_or_404
from story_maker.config import Config
from story_maker.observability.port import ObservabilityPort, Trace
from story_maker.pipeline.changes.confirm import ConfirmFailure, confirm_change
from story_maker.pipeline.changes.request import RequestFailure, request_change
from story_maker.pipeline.changes.selection import Selection
from story_maker.store.models import ChangeRequest, Novel


class RequestChangeOut(BaseModel):
    id: int
    proposal: dict[str, Any]
    affected_chapters: list[int]
    code: str
    expires_at: dt.datetime


class ConfirmChangeOut(BaseModel):
    run_id: int


def novel_for_change_request(session_factory: sessionmaker[Session], request_id: int) -> int | None:
    """La novela de una `SolicitudDeCambio`, para resolver la `Sesion` de `confirm_change` antes
    de comprobar si es del cliente (015-C16); `None` si el id no existe."""
    with session_factory() as session:
        row = session.get(ChangeRequest, request_id)
        return row.novel_id if row is not None else None


async def request_change_tool(
    *,
    session_factory: sessionmaker[Session],
    agent_port: AgentPort,
    telemetry: ObservabilityPort,
    config: Config,
    workspace: Path,
    clock: Clock,
    trace: Trace,
    user_id: int,
    novel_id: int,
    selection: Selection,
    request: str,
) -> RequestChangeOut:
    if not request.strip():
        _deny(session_factory, user_id, novel_id, "request_change", "la petición está vacía")
        from_http_exception(
            HTTPException(
                status_code=422, detail=field_error("request", "la petición no puede estar vacía")
            )
        )
    if len(request) > MAX_MESSAGE_CHARS:
        _deny(session_factory, user_id, novel_id, "request_change", "la petición es muy larga")
        from_http_exception(
            HTTPException(
                status_code=422,
                detail=field_error(
                    "request", f"la petición supera los {MAX_MESSAGE_CHARS} caracteres"
                ),
            )
        )
    with session_factory() as session:
        try:
            owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
        except HTTPException:
            _deny(session_factory, user_id, None, "request_change", NOT_FOUND_DETAIL)
            from_http_exception(HTTPException(status_code=404, detail=NOT_FOUND_DETAIL))
    prompt = (workspace / PLANNER_CHANGE_PROMPT_FILE).read_text(encoding="utf-8")
    outcome = await request_change(
        agent_port=agent_port,
        telemetry=ReuseTrace(telemetry, trace),
        session_factory=session_factory,
        config=config,
        prompt=prompt,
        novel_id=novel_id,
        user_id=user_id,
        selection=selection,
        request=request,
        now=clock(),
    )
    if isinstance(outcome, RequestFailure):
        _deny(session_factory, user_id, novel_id, "request_change", str(outcome.detail))
        from_http_exception(HTTPException(status_code=outcome.status, detail=outcome.detail))
    _allow(session_factory, user_id, novel_id, "request_change")
    return RequestChangeOut(
        id=outcome.id,
        proposal=outcome.proposal,
        affected_chapters=outcome.affected_chapters,
        code=outcome.code,
        expires_at=outcome.expires_at,
    )


def confirm_change_tool(
    *,
    session_factory: sessionmaker[Session],
    clock: Clock,
    user_id: int,
    request_id: int,
    code: str,
) -> ConfirmChangeOut:
    with session_factory() as session:
        row = session.get(ChangeRequest, request_id)
        novel = session.get(Novel, row.novel_id) if row is not None else None
        if row is None or novel is None or novel.user_id != user_id:
            _deny(session_factory, user_id, None, "confirm_change", NOT_FOUND_DETAIL)
            from_http_exception(HTTPException(status_code=404, detail=NOT_FOUND_DETAIL))
        novel_id = row.novel_id
    outcome = confirm_change(session_factory, request_id=request_id, code=code, now=clock())
    if isinstance(outcome, ConfirmFailure):
        _deny(session_factory, user_id, novel_id, "confirm_change", outcome.detail)
        from_http_exception(HTTPException(status_code=outcome.status, detail=outcome.detail))
    _allow(session_factory, user_id, novel_id, "confirm_change")
    return ConfirmChangeOut(run_id=outcome)


def _allow(session_factory: sessionmaker[Session], user_id: int, novel_id: int, tool: str) -> None:
    record_mcp_write(
        session_factory, user_id=user_id, novel_id=novel_id, tool=tool, decision="allow"
    )


def _deny(
    session_factory: sessionmaker[Session],
    user_id: int,
    novel_id: int | None,
    tool: str,
    reason: str,
) -> None:
    record_mcp_write(
        session_factory,
        user_id=user_id,
        novel_id=novel_id,
        tool=tool,
        decision="deny",
        rule=reason,
    )

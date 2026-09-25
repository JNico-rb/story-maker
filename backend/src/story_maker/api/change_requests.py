"""Rutas de las solicitudes de cambio: pedir (`POST /api/novels/{id}/change-requests`) y
confirmar (`POST /api/change-requests/{id}/confirm`) (`architecture.md` §10.1, §15.7; spec 014)."""

from __future__ import annotations

import datetime as dt
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from story_maker.api.dependencies import get_current_user_id
from story_maker.api.errors import field_error
from story_maker.api.interview import MAX_MESSAGE_CHARS
from story_maker.api.ownership import owned_or_404
from story_maker.pipeline.changes.confirm import ConfirmFailure, confirm_change
from story_maker.pipeline.changes.request import RequestFailure, request_change
from story_maker.pipeline.changes.selection import Selection
from story_maker.store.models import ChangeRequest, Novel

router = APIRouter()

PLANNER_CHANGE_PROMPT_FILE = "prompts/planner-change.md"


def _aware_utc(moment: dt.datetime) -> dt.datetime:
    """`expires_at` se guarda naive (UTC, `pipeline.runs.naive`); la API lo saca con huso
    (`architecture.md` §15.7, «Forma común»), 014-bug-C01c."""
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=dt.UTC)


class ChangeRequestIn(BaseModel):
    selection: Selection
    request: str


class ChangeRequestOut(BaseModel):
    id: int
    proposal: dict[str, Any]
    affected_chapters: list[int]
    code: str
    expires_at: dt.datetime


class ConfirmIn(BaseModel):
    code: str


class ConfirmOut(BaseModel):
    run_id: int


@router.post(
    "/api/novels/{novel_id}/change-requests", status_code=201, response_model=ChangeRequestOut
)
async def post_change_request(
    novel_id: int,
    body: ChangeRequestIn,
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
) -> ChangeRequestOut:
    if not body.request.strip():
        raise HTTPException(
            status_code=422, detail=field_error("request", "la petición no puede estar vacía")
        )
    if len(body.request) > MAX_MESSAGE_CHARS:
        raise HTTPException(
            status_code=422,
            detail=field_error("request", f"la petición supera los {MAX_MESSAGE_CHARS} caracteres"),
        )
    state = request.app.state
    with state.session_factory() as session:
        owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
    prompt = (state.workspace / PLANNER_CHANGE_PROMPT_FILE).read_text(encoding="utf-8")
    outcome = await request_change(
        agent_port=state.agent_port,
        telemetry=state.telemetry,
        session_factory=state.session_factory,
        config=state.config,
        prompt=prompt,
        novel_id=novel_id,
        user_id=user_id,
        selection=body.selection,
        request=body.request,
        now=state.clock(),
    )
    if isinstance(outcome, RequestFailure):
        raise HTTPException(status_code=outcome.status, detail=outcome.detail)
    return ChangeRequestOut(
        id=outcome.id,
        proposal=outcome.readable_proposal,
        affected_chapters=outcome.affected_chapters,
        code=outcome.code,
        expires_at=_aware_utc(outcome.expires_at),
    )


@router.post(
    "/api/change-requests/{request_id}/confirm", status_code=202, response_model=ConfirmOut
)
def post_confirm(
    request_id: int,
    body: ConfirmIn,
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
) -> ConfirmOut:
    state = request.app.state
    with state.session_factory() as session:
        owned_or_404(
            session,
            ChangeRequest,
            request_id,
            lambda row: session.get_one(Novel, row.novel_id).user_id == user_id,
        )
    outcome = confirm_change(
        state.session_factory, request_id=request_id, code=body.code, now=state.clock()
    )
    if isinstance(outcome, ConfirmFailure):
        raise HTTPException(status_code=outcome.status, detail=outcome.detail)
    return ConfirmOut(run_id=outcome)

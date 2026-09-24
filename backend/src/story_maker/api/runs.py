"""Ejecuciones: lanzar la generación y consultar su progreso por sondeo (`architecture.md` §15.7;
011-C01, C02, C04)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from story_maker.api.dependencies import get_current_user_id, get_session
from story_maker.api.ownership import owned_or_404
from story_maker.pipeline.queue import LaunchRejected, enqueue_generation
from story_maker.pipeline.runs import queue_position
from story_maker.store.models import Novel, RoleSession, Run
from story_maker.store.session import unit_of_work

router = APIRouter()


class EnqueuedResponse(BaseModel):
    run_id: int
    position: int


class ProgressResponse(BaseModel):
    run_id: int
    type: str
    status: str
    phase: str | None
    chapter: int | None
    cost_usd: float
    position: int | None
    reason: str | None
    reason_detail: str | None


@router.post("/api/novels/{novel_id}/runs", status_code=202, response_model=EnqueuedResponse)
def launch_generation(
    novel_id: int,
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)],
) -> EnqueuedResponse:
    owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
    state = request.app.state
    try:
        with unit_of_work(state.session_factory) as uow:
            run_id, position = enqueue_generation(uow, novel_id, now=state.clock())
    except LaunchRejected as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return EnqueuedResponse(run_id=run_id, position=position)


def owns_run(session: Session, user_id: int) -> Callable[[Run], bool]:
    return lambda run: session.get_one(Novel, run.novel_id).user_id == user_id


@router.get("/api/runs/{run_id}", response_model=ProgressResponse)
def poll_progress(
    run_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)],
) -> ProgressResponse:
    """Coste: la suma de las `SesionDeRol` de la ejecución; posición solo en `queued`; motivo y
    detalle solo en `failed` o `interrupted` (011-C04)."""
    run = owned_or_404(session, Run, run_id, owns_run(session, user_id))
    cost = session.query(func.coalesce(func.sum(RoleSession.cost_usd), 0.0)).filter(
        RoleSession.run_id == run.id
    )
    stopped = run.status in ("failed", "interrupted")
    return ProgressResponse(
        run_id=run.id,
        type=run.type,
        status=run.status,
        phase=run.phase,
        chapter=run.chapter,
        cost_usd=float(cost.scalar() or 0.0),
        position=queue_position(session, run),
        reason=run.reason if stopped else None,
        reason_detail=run.reason_detail if stopped else None,
    )

"""Ejecuciones: lanzar la generación y consultar su progreso por sondeo (`architecture.md` §15.7;
011-C01, C02, C04)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from story_maker.api.dependencies import get_current_user_id, get_session
from story_maker.api.ownership import owned_or_404
from story_maker.pipeline.queue import enqueue_generation
from story_maker.store.models import Novel
from story_maker.store.session import unit_of_work

router = APIRouter()


class EnqueuedResponse(BaseModel):
    run_id: int
    position: int


@router.post("/api/novels/{novel_id}/runs", status_code=202, response_model=EnqueuedResponse)
def launch_generation(
    novel_id: int,
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)],
) -> EnqueuedResponse:
    owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
    state = request.app.state
    with unit_of_work(state.session_factory) as uow:
        run_id, position = enqueue_generation(uow, novel_id, now=state.clock())
    return EnqueuedResponse(run_id=run_id, position=position)

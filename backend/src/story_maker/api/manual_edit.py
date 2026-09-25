"""Rutas de la edición manual: el lint en vivo (`POST /api/novels/{id}/chapters/{n}/lint`) y el
guardado (`PUT /api/novels/{id}/chapters/{n}`) (`architecture.md` §10.3, §15.7; spec 019)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi import Path as PathParam
from pydantic import BaseModel

from story_maker.api.dependencies import get_current_user_id
from story_maker.api.ownership import owned_or_404
from story_maker.domain.constants import CHAPTERS_PER_NOVEL
from story_maker.pipeline.manual_edit.live_lint import live_lint
from story_maker.pipeline.manual_edit.save import SaveRejected, save_edit
from story_maker.store.models import Novel
from story_maker.store.versions import current_version

router = APIRouter()

ChapterNumber = Annotated[int, PathParam(ge=1, le=CHAPTERS_PER_NOVEL)]
NO_PUBLISHED_VERSION = "la novela no tiene ninguna versión publicada"


class LintIn(BaseModel):
    text: str


class LintOut(BaseModel):
    diagnostics: list[dict[str, Any]]


@router.post("/api/novels/{novel_id}/chapters/{chapter}/lint", response_model=LintOut)
def post_lint(
    novel_id: int,
    chapter: ChapterNumber,
    body: LintIn,
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
) -> LintOut:
    """Solo lecturas: ni SQLite, ni audit log, ni traza (019-I2)."""
    state = request.app.state
    with state.session_factory() as session:
        novel = owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
        current = current_version(session, novel_id)
        if current is None:
            raise HTTPException(status_code=409, detail=NO_PUBLISHED_VERSION)
        found = live_lint(session, state.config, novel, current.id, chapter, body.text)
    return LintOut(diagnostics=[d.to_json() for d in found])


class SaveIn(BaseModel):
    text: str
    base_version: int


class SaveOut(BaseModel):
    run_id: int


@router.put("/api/novels/{novel_id}/chapters/{chapter}", status_code=202, response_model=SaveOut)
def put_chapter(
    novel_id: int,
    chapter: ChapterNumber,
    body: SaveIn,
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
) -> SaveOut:
    state = request.app.state
    with state.session_factory() as session:
        owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
    outcome = save_edit(
        state.session_factory,
        novel_id=novel_id,
        chapter=chapter,
        text=body.text,
        base_version=body.base_version,
        now=state.clock(),
    )
    if isinstance(outcome, SaveRejected):
        raise HTTPException(status_code=outcome.status, detail=outcome.detail)
    return SaveOut(run_id=outcome)

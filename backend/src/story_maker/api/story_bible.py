"""`GET /api/novels/{id}/story-bible?version={v}`: la story bible de una versión publicada del
propio cliente; sin `version`, la vigente (`architecture.md` §15.7, §18; 009-C25 a 009-C27)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from story_maker.api.dependencies import get_current_user_id, get_session
from story_maker.api.ownership import NOT_FOUND_DETAIL, owned_or_404
from story_maker.store.models import Novel
from story_maker.store.story_bible import StoryBible, read_story_bible
from story_maker.store.versions import current_version

router = APIRouter()


class StoryBibleResponse(BaseModel):
    version: int
    story_bible: StoryBible


@router.get("/api/novels/{novel_id}/story-bible", response_model=StoryBibleResponse)
def get_story_bible(
    novel_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)],
) -> StoryBibleResponse:
    novel = owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
    version = current_version(session, novel.id)
    if version is None or version.number is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    return StoryBibleResponse(
        version=version.number, story_bible=read_story_bible(session, version.id)
    )

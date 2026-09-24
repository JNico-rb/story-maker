"""Rutas del brief: lectura con sus comprobaciones (008-C01, 008-C09 a 008-C17)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from story_maker.api.dependencies import get_current_user_id
from story_maker.api.ownership import owned_or_404
from story_maker.domain.brief import BriefContent, missing_fields
from story_maker.interview.novels import brief_of
from story_maker.store.models import Brief, Novel

router = APIRouter()


class BriefOut(BaseModel):
    status: Literal["draft", "confirmed"]
    missing_fields: list[str]


def build_brief_out(brief: Brief) -> BriefOut:
    content = BriefContent.model_validate(brief.content) if brief.content else BriefContent()
    return BriefOut(status=brief.status, missing_fields=missing_fields(content))


@router.get("/api/novels/{novel_id}/brief", response_model=BriefOut)
def get_brief(
    novel_id: int, request: Request, user_id: int = Depends(get_current_user_id)
) -> BriefOut:
    session = request.app.state.session_factory()
    try:
        owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
        brief = brief_of(session, novel_id)
        return build_brief_out(brief)
    finally:
        session.close()

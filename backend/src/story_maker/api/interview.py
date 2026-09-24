"""Rutas de la entrevista: historial de mensajes (008-C01, 008-C03)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from story_maker.api.dependencies import get_current_user_id
from story_maker.api.ownership import owned_or_404
from story_maker.store.models import Interview, InterviewMessage, Novel

router = APIRouter()


class InterviewMessageOut(BaseModel):
    author: Literal["user", "interviewer"]
    text: str


@router.get("/api/novels/{novel_id}/interview/messages", response_model=list[InterviewMessageOut])
def get_interview_messages(
    novel_id: int, request: Request, user_id: int = Depends(get_current_user_id)
) -> list[InterviewMessageOut]:
    session = request.app.state.session_factory()
    try:
        novel = owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
        interview = session.query(Interview).filter(Interview.novel_id == novel.id).one()
        rows = (
            session.query(InterviewMessage)
            .filter(InterviewMessage.interview_id == interview.id)
            .order_by(InterviewMessage.id)
            .all()
        )
        return [InterviewMessageOut(author=row.author, text=row.text) for row in rows]
    finally:
        session.close()

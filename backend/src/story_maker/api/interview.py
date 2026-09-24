"""Rutas de la entrevista: historial de mensajes y turnos (008-C01, 008-C03 a 008-C08)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from story_maker.api.brief import BriefOut, build_brief_out
from story_maker.api.dependencies import get_current_user_id
from story_maker.api.ownership import owned_or_404
from story_maker.interview.brief import TurnFailure, run_turn
from story_maker.interview.novels import brief_of
from story_maker.store.models import Interview, InterviewMessage, Novel

router = APIRouter()

INTERVIEWER_PROMPT_FILE = "prompts/interviewer.md"


class InterviewMessageOut(BaseModel):
    author: Literal["user", "interviewer"]
    text: str


class InterviewMessageIn(BaseModel):
    text: str


class TurnOut(BaseModel):
    reply: str
    brief: BriefOut


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


@router.post("/api/novels/{novel_id}/interview/messages", response_model=TurnOut)
async def post_interview_message(
    novel_id: int,
    body: InterviewMessageIn,
    request: Request,
    user_id: int = Depends(get_current_user_id),
) -> TurnOut:
    state = request.app.state
    session = state.session_factory()
    try:
        owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
    finally:
        session.close()

    prompt = (state.workspace / INTERVIEWER_PROMPT_FILE).read_text(encoding="utf-8")
    outcome = await run_turn(
        agent_port=state.agent_port,
        telemetry=state.telemetry,
        session_factory=state.session_factory,
        prompt=prompt,
        novel_id=novel_id,
        user_id=user_id,
        text=body.text,
        now=state.clock(),
    )
    if isinstance(outcome, TurnFailure):
        raise HTTPException(status_code=outcome.status, detail=outcome.reason)

    session = state.session_factory()
    try:
        brief = brief_of(session, novel_id)
        return TurnOut(reply=outcome.reply, brief=build_brief_out(brief))
    finally:
        session.close()

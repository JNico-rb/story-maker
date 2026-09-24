"""Rutas del brief: lectura con sus comprobaciones y confirmación (008-C01, 008-C09 a 008-C17)."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from story_maker.api.dependencies import get_current_user_id
from story_maker.api.ownership import owned_or_404
from story_maker.domain.brief import BriefContent, Contradiccion, all_contradictions, missing_fields
from story_maker.interview.novels import brief_of, load_accepted_facts, load_banned_entries
from story_maker.store.models import Brief, Novel
from story_maker.store.session import unit_of_work

router = APIRouter()


class BriefOut(BaseModel):
    status: Literal["draft", "confirmed"]
    content: BriefContent
    missing_fields: list[str]
    contradictions: list[Contradiccion]


def build_brief_out(session: Session, brief: Brief, novel: Novel) -> BriefOut:
    content = BriefContent.model_validate(brief.content) if brief.content else BriefContent()
    banned_entries = load_banned_entries(session, novel.user_id, novel.id)
    accepted_facts = load_accepted_facts(session, novel.id)
    return BriefOut(
        status=brief.status,
        content=content,
        missing_fields=missing_fields(content),
        contradictions=all_contradictions(
            content, novel.created_at.date(), banned_entries, accepted_facts
        ),
    )


def _missing_field_problems(content: BriefContent) -> list[dict[str, Any]]:
    return [
        {
            "loc": ["body", "brief", "missing_fields", name],
            "msg": f"falta: {name}",
            "type": "missing_field",
        }
        for name in missing_fields(content)
    ]


def _contradiction_problems(contradictions: list[Contradiccion]) -> list[dict[str, Any]]:
    return [
        {
            "loc": ["body", "brief", "contradictions", *item.fields],
            "msg": f"contradicción {item.rule}",
            "type": "contradiction",
        }
        for item in contradictions
    ]


def brief_problems(brief_out: BriefOut) -> list[dict[str, Any]]:
    """Todo lo que bloquea la confirmación (008-C09 a 008-C13); cada paso añade su comprobación."""
    return _missing_field_problems(brief_out.content) + _contradiction_problems(
        brief_out.contradictions
    )


@router.get("/api/novels/{novel_id}/brief", response_model=BriefOut)
def get_brief(
    novel_id: int, request: Request, user_id: int = Depends(get_current_user_id)
) -> BriefOut:
    session = request.app.state.session_factory()
    try:
        novel = owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
        brief = brief_of(session, novel_id)
        return build_brief_out(session, brief, novel)
    finally:
        session.close()


@router.post("/api/novels/{novel_id}/brief/confirm", response_model=BriefOut)
def confirm_brief(
    novel_id: int, request: Request, user_id: int = Depends(get_current_user_id)
) -> BriefOut:
    state = request.app.state
    session = state.session_factory()
    try:
        novel = owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
        brief = brief_of(session, novel_id)
        if brief.status == "confirmed":
            raise HTTPException(status_code=409, detail="el brief ya está confirmado")
        brief_out = build_brief_out(session, brief, novel)
        problems = brief_problems(brief_out)
        if problems:
            raise HTTPException(status_code=422, detail=problems)
    finally:
        session.close()

    with unit_of_work(state.session_factory) as uow:
        fresh = uow.session.query(Brief).filter(Brief.novel_id == novel_id).one()
        fresh.status = "confirmed"

    session = state.session_factory()
    try:
        novel = owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
        return build_brief_out(session, brief_of(session, novel_id), novel)
    finally:
        session.close()

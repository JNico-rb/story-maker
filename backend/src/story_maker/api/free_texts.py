"""Rutas de los textos libres: extraer hechos con el extractor (008-C18 a 008-C23)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from story_maker.api.dependencies import get_current_user_id
from story_maker.api.errors import field_error
from story_maker.api.ownership import owned_or_404
from story_maker.domain.brief import BriefContent, valid_subjects
from story_maker.interview.free_text import (
    MAX_FREE_TEXT_CHARS,
    FreeTextFailure,
    run_free_text,
)
from story_maker.interview.novels import brief_of
from story_maker.store.models import Novel

router = APIRouter()

EXTRACTOR_PROMPT_FILE = "prompts/extractor.md"


class FreeTextIn(BaseModel):
    content: str


class VerifiedFactOut(BaseModel):
    id: int
    subject: str
    attribute: str
    value: str
    quote: str
    accepted: bool | None
    mandatory: bool


class FreeTextOut(BaseModel):
    free_text_id: int
    verified_facts: list[VerifiedFactOut]


@router.post("/api/novels/{novel_id}/free-texts", status_code=201, response_model=FreeTextOut)
async def post_free_text(
    novel_id: int,
    body: FreeTextIn,
    request: Request,
    user_id: int = Depends(get_current_user_id),
) -> FreeTextOut:
    if not body.content.strip():
        raise HTTPException(
            status_code=422, detail=field_error("content", "el texto no puede estar vacío")
        )
    if len(body.content) > MAX_FREE_TEXT_CHARS:
        raise HTTPException(
            status_code=422,
            detail=field_error("content", f"el texto supera los {MAX_FREE_TEXT_CHARS} caracteres"),
        )

    state = request.app.state
    session = state.session_factory()
    try:
        owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
        brief = brief_of(session, novel_id)
        if brief.status == "confirmed":
            raise HTTPException(status_code=409, detail="el brief ya está confirmado")
        content = BriefContent.model_validate(brief.content) if brief.content else BriefContent()
        if not valid_subjects(content):
            raise HTTPException(
                status_code=409, detail="el brief todavía no tiene ningún sujeto válido"
            )
    finally:
        session.close()

    prompt = (state.workspace / EXTRACTOR_PROMPT_FILE).read_text(encoding="utf-8")
    outcome = await run_free_text(
        agent_port=state.agent_port,
        telemetry=state.telemetry,
        policy=state.policy,
        session_factory=state.session_factory,
        prompt=prompt,
        novel_id=novel_id,
        user_id=user_id,
        text=body.content,
        now=state.clock(),
    )
    if isinstance(outcome, FreeTextFailure):
        raise HTTPException(status_code=outcome.status, detail=outcome.reason)

    return FreeTextOut(
        free_text_id=outcome.free_text_id,
        verified_facts=[
            VerifiedFactOut(
                id=f.id,
                subject=f.subject,
                attribute=f.attribute,
                value=f.value,
                quote=f.quote,
                accepted=f.accepted,
                mandatory=f.mandatory,
            )
            for f in outcome.verified_facts
        ],
    )

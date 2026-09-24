"""Rutas del brief: lectura con sus comprobaciones y confirmación (008-C01, 008-C09 a 008-C17)."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from story_maker.api.dependencies import get_current_user_id
from story_maker.api.errors import field_error
from story_maker.api.ownership import owned_or_404
from story_maker.domain.brief import (
    BriefContent,
    Contradiccion,
    ElementoPersonal,
    SchemaError,
    all_contradictions,
    mandatory_count,
    missing_fields,
    personal_elements,
    schema_errors,
)
from story_maker.interview.brief import interview_trace_key
from story_maker.interview.novels import brief_of, load_accepted_facts, load_banned_entries
from story_maker.store.models import Brief, ExtractedFact, FreeText, Novel
from story_maker.store.session import unit_of_work

router = APIRouter()


class BriefOut(BaseModel):
    status: Literal["draft", "confirmed"]
    content: BriefContent
    missing_fields: list[str]
    contradictions: list[Contradiccion]
    schema_errors: list[SchemaError]
    mandatory_count: int
    max_mandatory_elements: int
    personal_elements: list[ElementoPersonal]


def build_brief_out(
    session: Session, brief: Brief, novel: Novel, max_mandatory_elements: int
) -> BriefOut:
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
        schema_errors=schema_errors(content, accepted_facts),
        mandatory_count=mandatory_count(content, accepted_facts),
        max_mandatory_elements=max_mandatory_elements,
        personal_elements=personal_elements(content, accepted_facts),
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


def _mandatory_cap_problems(brief_out: BriefOut) -> list[dict[str, Any]]:
    if brief_out.mandatory_count <= brief_out.max_mandatory_elements:
        return []
    msg = f"{brief_out.mandatory_count} de {brief_out.max_mandatory_elements}"
    return [{"loc": ["body", "brief", "mandatory_count"], "msg": msg, "type": "mandatory_cap"}]


def _schema_error_problems(errors: list[SchemaError]) -> list[dict[str, Any]]:
    return [
        {"loc": ["body", "brief", *item.fields], "msg": item.message, "type": "schema_error"}
        for item in errors
    ]


def brief_problems(brief_out: BriefOut) -> list[dict[str, Any]]:
    """Todo lo que bloquea la confirmación (008-C09 a 008-C13)."""
    return (
        _missing_field_problems(brief_out.content)
        + _contradiction_problems(brief_out.contradictions)
        + _schema_error_problems(brief_out.schema_errors)
        + _mandatory_cap_problems(brief_out)
    )


def _record_schema_brief_score(state: Any, novel_id: int, problems: list[dict[str, Any]]) -> None:
    """`schema-brief`: 1 si pasa, 0 con los problemas en el comentario; un intento por
    confirmación, en la traza `entrevista` de la novela (008-C15, 008-C16, 008-C31)."""
    comment = "; ".join(str(item["msg"]) for item in problems) if problems else None
    with state.telemetry.trace(
        interview_trace_key(novel_id), name="entrevista", session=str(novel_id)
    ) as trace:
        state.telemetry.score(trace, "schema-brief", 0 if problems else 1, comment=comment)


@router.get("/api/novels/{novel_id}/brief", response_model=BriefOut)
def get_brief(
    novel_id: int, request: Request, user_id: int = Depends(get_current_user_id)
) -> BriefOut:
    state = request.app.state
    session = state.session_factory()
    try:
        novel = owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
        brief = brief_of(session, novel_id)
        return build_brief_out(session, brief, novel, state.config.max_mandatory_elements)
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
        brief_out = build_brief_out(session, brief, novel, state.config.max_mandatory_elements)
        problems = brief_problems(brief_out)
        _record_schema_brief_score(state, novel_id, problems)
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
        return build_brief_out(
            session, brief_of(session, novel_id), novel, state.config.max_mandatory_elements
        )
    finally:
        session.close()


class ExtractedFactPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    accepted: bool | None = None
    mandatory: bool | None = None


def _verified_fact_or_404(session: Session, novel_id: int, fact_id: int) -> ExtractedFact:
    fact = (
        session.query(ExtractedFact)
        .join(FreeText, ExtractedFact.free_text_id == FreeText.id)
        .filter(
            FreeText.novel_id == novel_id,
            ExtractedFact.id == fact_id,
            ExtractedFact.verified.is_(True),
        )
        .one_or_none()
    )
    if fact is None:
        raise HTTPException(status_code=404, detail="no encontrado")
    return fact


@router.patch("/api/novels/{novel_id}/brief/extracted-facts/{fact_id}", response_model=BriefOut)
def patch_extracted_fact(
    novel_id: int,
    fact_id: int,
    body: ExtractedFactPatch,
    request: Request,
    user_id: int = Depends(get_current_user_id),
) -> BriefOut:
    """Acepta, rechaza o marca obligatorio un hecho extraído verificado (008-C24); solo el
    cliente decide esto, nunca `update_brief` (008-C05)."""
    state = request.app.state
    session = state.session_factory()
    try:
        owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
        brief = brief_of(session, novel_id)
        if brief.status == "confirmed":
            raise HTTPException(status_code=409, detail="el brief ya está confirmado")
        fact = _verified_fact_or_404(session, novel_id, fact_id)
        new_accepted = body.accepted if body.accepted is not None else bool(fact.accepted)
        new_mandatory = body.mandatory if body.mandatory is not None else fact.mandatory
        if new_mandatory and not new_accepted:
            raise HTTPException(
                status_code=422,
                detail=field_error("mandatory", "un hecho sin aceptar no puede ser obligatorio"),
            )
    finally:
        session.close()

    with unit_of_work(state.session_factory) as uow:
        fresh = uow.session.get(ExtractedFact, fact_id)
        if fresh is not None:
            if body.accepted is not None:
                fresh.accepted = body.accepted
                if body.accepted is False:
                    fresh.mandatory = False
            if body.mandatory is not None:
                fresh.mandatory = body.mandatory

    session = state.session_factory()
    try:
        novel = owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
        return build_brief_out(
            session, brief_of(session, novel_id), novel, state.config.max_mandatory_elements
        )
    finally:
        session.close()

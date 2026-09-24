"""Listas prohibidas: nivel `user` del cliente y nivel `novel` de una novela (008-C25, 008-C26)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from story_maker.api.dependencies import get_current_user_id
from story_maker.api.errors import field_error
from story_maker.api.ownership import owned_or_404
from story_maker.interview.banned_terms import InvalidBannedTerm, add_banned_term
from story_maker.interview.novels import brief_of
from story_maker.store.models import BannedTerm, Novel
from story_maker.store.session import unit_of_work

router = APIRouter()


class BannedTermOut(BaseModel):
    id: int
    term: str
    type: Literal["word", "topic"]
    level: Literal["global", "user", "novel"]
    keywords: list[str]
    normalized: str


class BannedTermIn(BaseModel):
    term: str
    type: Literal["word", "topic"]
    keywords: list[str] = []


def _out(row: BannedTerm) -> BannedTermOut:
    return BannedTermOut(
        id=row.id,
        term=row.term,
        type=row.type,
        level=row.level,
        keywords=list(row.keywords or []),
        normalized=row.normalized,
    )


# --- Nivel `user`: en cualquier estado de las novelas del cliente (008-C26) --------------------


@router.get("/api/banned-terms", response_model=list[BannedTermOut])
def get_user_banned_terms(
    request: Request, user_id: int = Depends(get_current_user_id)
) -> list[BannedTermOut]:
    session = request.app.state.session_factory()
    try:
        rows = (
            session.query(BannedTerm)
            .filter(BannedTerm.level == "user", BannedTerm.user_id == user_id)
            .order_by(BannedTerm.id)
            .all()
        )
        return [_out(row) for row in rows]
    finally:
        session.close()


@router.post("/api/banned-terms", status_code=201, response_model=BannedTermOut)
def post_user_banned_term(
    body: BannedTermIn, request: Request, user_id: int = Depends(get_current_user_id)
) -> BannedTermOut:
    state = request.app.state
    try:
        with unit_of_work(state.session_factory) as uow:
            row = add_banned_term(
                uow,
                level="user",
                user_id=user_id,
                novel_id=None,
                term=body.term,
                type_=body.type,
                keywords=body.keywords,
            )
    except InvalidBannedTerm as exc:
        raise HTTPException(status_code=422, detail=field_error("term", str(exc))) from exc
    if row is None:
        raise HTTPException(status_code=409, detail="ya existe una entrada igual")
    return _out(row)


@router.delete("/api/banned-terms/{term_id}", status_code=204)
def delete_user_banned_term(
    term_id: int, request: Request, user_id: int = Depends(get_current_user_id)
) -> None:
    state = request.app.state
    session = state.session_factory()
    try:
        owned_or_404(
            session,
            BannedTerm,
            term_id,
            lambda t: t.level == "user" and t.user_id == user_id,
        )
    finally:
        session.close()

    with unit_of_work(state.session_factory) as uow:
        row = uow.session.get(BannedTerm, term_id)
        if row is not None:
            uow.delete(row)


# --- Nivel `novel`: la que declara la entrevista, editable antes de confirmar (008-C25) --------


def _owned_novel_or_404(session: Session, novel_id: int, user_id: int) -> Novel:
    return owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)


@router.get("/api/novels/{novel_id}/banned-terms", response_model=list[BannedTermOut])
def get_novel_banned_terms(
    novel_id: int, request: Request, user_id: int = Depends(get_current_user_id)
) -> list[BannedTermOut]:
    session = request.app.state.session_factory()
    try:
        _owned_novel_or_404(session, novel_id, user_id)
        rows = (
            session.query(BannedTerm)
            .filter(BannedTerm.level == "novel", BannedTerm.novel_id == novel_id)
            .order_by(BannedTerm.id)
            .all()
        )
        return [_out(row) for row in rows]
    finally:
        session.close()


@router.post("/api/novels/{novel_id}/banned-terms", status_code=201, response_model=BannedTermOut)
def post_novel_banned_term(
    novel_id: int,
    body: BannedTermIn,
    request: Request,
    user_id: int = Depends(get_current_user_id),
) -> BannedTermOut:
    state = request.app.state
    session = state.session_factory()
    try:
        _owned_novel_or_404(session, novel_id, user_id)
        if brief_of(session, novel_id).status == "confirmed":
            raise HTTPException(status_code=409, detail="el brief ya está confirmado")
    finally:
        session.close()

    try:
        with unit_of_work(state.session_factory) as uow:
            row = add_banned_term(
                uow,
                level="novel",
                user_id=None,
                novel_id=novel_id,
                term=body.term,
                type_=body.type,
                keywords=body.keywords,
            )
    except InvalidBannedTerm as exc:
        raise HTTPException(status_code=422, detail=field_error("term", str(exc))) from exc
    if row is None:
        raise HTTPException(status_code=409, detail="ya existe una entrada igual")
    return _out(row)


@router.delete("/api/novels/{novel_id}/banned-terms/{term_id}", status_code=204)
def delete_novel_banned_term(
    novel_id: int,
    term_id: int,
    request: Request,
    user_id: int = Depends(get_current_user_id),
) -> None:
    state = request.app.state
    session = state.session_factory()
    try:
        _owned_novel_or_404(session, novel_id, user_id)
        if brief_of(session, novel_id).status == "confirmed":
            raise HTTPException(status_code=409, detail="el brief ya está confirmado")
        owned_or_404(
            session,
            BannedTerm,
            term_id,
            lambda t: t.level == "novel" and t.novel_id == novel_id,
        )
    finally:
        session.close()

    with unit_of_work(state.session_factory) as uow:
        row = uow.session.get(BannedTerm, term_id)
        if row is not None:
            uow.delete(row)

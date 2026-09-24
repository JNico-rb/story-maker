"""Rutas de novelas: crear para entrevistar, listar y ver el detalle (008-C01, 008-C02)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from story_maker.api.dependencies import get_current_user_id
from story_maker.api.ownership import owned_or_404
from story_maker.interview.novels import (
    NovelSummary,
    create_interview_novel,
    list_novels,
    novel_summary,
)
from story_maker.store.models import Novel

router = APIRouter()


@router.post("/api/novels", status_code=201, response_model=NovelSummary)
def post_novel(request: Request, user_id: int = Depends(get_current_user_id)) -> NovelSummary:
    """Cuerpo vacío: crea la novela para entrevistarla (008-C01); con un brief, la importa
    (008-C28)."""
    state = request.app.state
    novel_id = create_interview_novel(
        state.session_factory,
        user_id=user_id,
        embedding_model=state.config.embedding_model,
        created_at=state.clock(),
    )
    session = state.session_factory()
    try:
        novel = session.get(Novel, novel_id)
        if novel is None:  # pragma: no cover - se acaba de crear en la misma unidad de trabajo
            raise LookupError(f"novela {novel_id} no encontrada tras crearla")
        return novel_summary(session, novel)
    finally:
        session.close()


@router.get("/api/novels", response_model=list[NovelSummary])
def get_novels(request: Request, user_id: int = Depends(get_current_user_id)) -> list[NovelSummary]:
    session = request.app.state.session_factory()
    try:
        return list_novels(session, user_id)
    finally:
        session.close()


@router.get("/api/novels/{novel_id}", response_model=NovelSummary)
def get_novel(
    novel_id: int, request: Request, user_id: int = Depends(get_current_user_id)
) -> NovelSummary:
    session = request.app.state.session_factory()
    try:
        novel = owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
        return novel_summary(session, novel)
    finally:
        session.close()

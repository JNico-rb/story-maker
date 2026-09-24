"""`GET /api/novels/{id}/versions[/{v}][/pdf]`: historial publicado, detalle de una versión
publicada como la misma `VistaDeVersion` en datos, y su PDF servido tal cual (013-C11 a 013-C15).

Solo lo publicado: una candidata no tiene número, así que la ruta por número nunca la alcanza
(009-I1) — se trata como inexistente, igual que 002 trata lo ajeno (013-C15)."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Path as PathParam
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from story_maker.api.dependencies import get_current_user_id, get_session
from story_maker.api.ownership import NOT_FOUND_DETAIL, owned_or_404
from story_maker.render.version_view import VersionViewData
from story_maker.render.view_data import load_version_view_data
from story_maker.store.models import Novel, Version
from story_maker.store.versions import published_version

router = APIRouter()

VersionNumber = Annotated[int, PathParam(ge=1)]


class VersionSummary(BaseModel):
    number: int
    published_at: dt.datetime
    changed_chapters: list[int]


class VersionsListResponse(BaseModel):
    versions: list[VersionSummary]


class VersionDetailResponse(BaseModel):
    version: int
    view: VersionViewData


def _owned_novel(session: Session, novel_id: int, user_id: int) -> Novel:
    novel: Novel = owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
    return novel


def _published_or_404(session: Session, novel_id: int, number: int) -> Version:
    version = published_version(session, novel_id, number)
    if version is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    return version


@router.get("/api/novels/{novel_id}/versions", response_model=VersionsListResponse)
def list_versions(
    novel_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)],
) -> VersionsListResponse:
    novel = _owned_novel(session, novel_id, user_id)
    rows = (
        session.query(Version)
        .filter(Version.novel_id == novel.id, Version.status == "published")
        .order_by(Version.number)
        .all()
    )
    return VersionsListResponse(
        versions=[
            # publicada: number y published_at siempre asignados (ck_versions_published_fields).
            VersionSummary(
                number=v.number,
                published_at=v.published_at,
                changed_chapters=list(v.changed_chapters),
            )
            for v in rows
        ]
    )


@router.get("/api/novels/{novel_id}/versions/{number}", response_model=VersionDetailResponse)
def get_version(
    novel_id: int,
    number: VersionNumber,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)],
) -> VersionDetailResponse:
    novel = _owned_novel(session, novel_id, user_id)
    version = _published_or_404(session, novel.id, number)
    return VersionDetailResponse(version=number, view=load_version_view_data(session, version))


@router.get("/api/novels/{novel_id}/versions/{number}/pdf")
def get_version_pdf(
    novel_id: int,
    number: VersionNumber,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)],
) -> FileResponse:
    novel = _owned_novel(session, novel_id, user_id)
    version = _published_or_404(session, novel.id, number)
    if version.pdf_path is None or not Path(version.pdf_path).is_file():
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    return FileResponse(version.pdf_path, media_type="application/pdf")

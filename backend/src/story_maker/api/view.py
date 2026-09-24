"""`GET /view/versions/{version_id}?token=...`: exige el token de vista antes de tocar nada más
— ni siquiera revela si la versión existe (013-C07, 013-I2) — y sirve la `VistaDeVersion` de esa
versión, candidata o publicada (013-C01 a 013-C05)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from story_maker.api.dependencies import get_session
from story_maker.api.ownership import NOT_FOUND_DETAIL
from story_maker.api.view_tokens import ViewTokenError, decode_view_token
from story_maker.render.version_view import render_version_view
from story_maker.render.view_data import load_version_view_data
from story_maker.store.models import Version

router = APIRouter()

UNAUTHORIZED_DETAIL = "no autorizado"


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=401, detail=UNAUTHORIZED_DETAIL)


@router.get("/view/versions/{version_id}", response_class=HTMLResponse)
def view_version(
    version_id: int,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    token: str | None = None,
) -> HTMLResponse:
    if token is None:
        raise _unauthorized()

    state = request.app.state
    try:
        token_version_id = decode_view_token(token, state.jwt_secret, now=state.clock())
    except ViewTokenError:
        raise _unauthorized() from None
    if token_version_id != version_id:
        raise _unauthorized()

    version = session.get(Version, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    data = load_version_view_data(session, version)
    return HTMLResponse(render_version_view(data))

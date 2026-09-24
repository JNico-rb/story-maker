"""`GET /view/versions/{version_id}?token=...`: exige el token de vista antes de tocar nada más
— ni siquiera revela si la versión existe (013-C07, 013-I2). El render en sí (013-C01 a 013-C05)
espera al repositorio de 009-story-bible-y-versiones."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from story_maker.api.view_tokens import ViewTokenError, decode_view_token

router = APIRouter()

UNAUTHORIZED_DETAIL = "no autorizado"


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=401, detail=UNAUTHORIZED_DETAIL)


@router.get("/view/versions/{version_id}")
def view_version(version_id: int, request: Request, token: str | None = None) -> str:
    if token is None:
        raise _unauthorized()

    state = request.app.state
    try:
        token_version_id = decode_view_token(token, state.jwt_secret, now=state.clock())
    except ViewTokenError:
        raise _unauthorized() from None
    if token_version_id != version_id:
        raise _unauthorized()

    # Token válido para esta versión: pendiente el render desde SQLite (013-C01 a 013-C05),
    # bloqueado en la 009-story-bible-y-versiones (ver TODO.md, bloque 013).
    raise NotImplementedError("VistaDeVersion pendiente de 009-story-bible-y-versiones")

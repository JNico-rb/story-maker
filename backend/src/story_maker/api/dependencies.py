"""Dependencia del cliente actual: el único punto que decide identidad desde el
`TokenDeAcceso` (002-C11 a 002-C15, I2, I4, I5)."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from story_maker.api.auth import AuthError, decode_access_token
from story_maker.store.models import User

UNAUTHORIZED_DETAIL = "no autorizado"


def _unauthorized() -> HTTPException:
    """Mismo código y mismo cuerpo para cualquier causa (002-C12, 002-C13)."""
    return HTTPException(
        status_code=401, detail=UNAUTHORIZED_DETAIL, headers={"WWW-Authenticate": "Bearer"}
    )


def get_session(request: Request) -> Iterator[Session]:
    """Dependencia de sesión, para las rutas de recurso que las specs siguientes añaden."""
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_current_user_id(request: Request) -> int:
    """El cliente de la petición sale solo del token (002-I4): nunca de cuerpo, query o cabecera
    distinta de `Authorization`."""
    header = request.headers.get("authorization")
    if header is None:
        raise _unauthorized()
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise _unauthorized()

    state = request.app.state
    try:
        user_id = decode_access_token(token, state.jwt_secret, now=state.clock())
    except AuthError:
        raise _unauthorized() from None

    session = state.session_factory()
    try:
        if session.get(User, user_id) is None:
            raise _unauthorized()
    finally:
        session.close()
    return user_id

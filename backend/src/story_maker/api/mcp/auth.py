"""Identidad de `/mcp`: el mismo `TokenDeAcceso` de la cabecera `Authorization`, verificado con
el mismo `decode_access_token` que usa `/api` (002-I5, 015-I3, 015-C02, 015-C03).

El transporte MCP no es una ruta FastAPI corriente (fastmcp monta su propio manejador ASGI), así
que la identidad no puede pasar por `Depends(get_current_user_id)`: este middleware ASGI hace la
misma comprobación, antes de que la petición llegue al protocolo MCP, y dejaría exactamente 401
sin ejecutar nada (015-C02) — la sesión de la petición ni se abre ni se ejecuta ninguna tool."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy.orm import Session, sessionmaker
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from story_maker.api.auth import AuthError, Clock, decode_access_token
from story_maker.api.dependencies import UNAUTHORIZED_DETAIL
from story_maker.store.models import User

Send_ = Callable[[dict[str, Any]], Awaitable[None]]


def _unauthorized_response() -> JSONResponse:
    """Mismo cuerpo y cabecera que `_unauthorized()` de `api/dependencies.py` (015-C02)."""
    return JSONResponse(
        {"detail": UNAUTHORIZED_DETAIL},
        status_code=401,
        headers={"WWW-Authenticate": "Bearer"},
    )


def authenticate(
    request: Request,
    *,
    session_factory: sessionmaker[Session],
    jwt_secret: str,
    clock: Clock,
) -> int | None:
    """El id del cliente del token de esta petición, o `None` si no es válido (015-I3)."""
    header = request.headers.get("authorization")
    if header is None:
        return None
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    try:
        user_id = decode_access_token(token, jwt_secret, now=clock())
    except AuthError:
        return None
    with session_factory() as session:
        if session.get(User, user_id) is None:
            return None
    return user_id


class BearerAuthMiddleware:
    """ASGI puro: sin `TokenDeAcceso` válido, 401 antes de que fastmcp vea la petición
    (015-C02). Con uno válido, dispone `user_id` en `scope['state']` para que cada tool lo lea
    (`fastmcp.server.dependencies.get_http_request().state.user_id`, 015-C03)."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        session_factory: sessionmaker[Session],
        jwt_secret: str,
        clock: Clock,
    ) -> None:
        self.app = app
        self.session_factory = session_factory
        self.jwt_secret = jwt_secret
        self.clock = clock

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope, receive=receive)
        user_id = authenticate(
            request,
            session_factory=self.session_factory,
            jwt_secret=self.jwt_secret,
            clock=self.clock,
        )
        if user_id is None:
            await _unauthorized_response()(scope, receive, send)
            return
        scope.setdefault("state", {})["user_id"] = user_id
        await self.app(scope, receive, send)

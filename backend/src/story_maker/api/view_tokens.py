"""Token de vista: JWT distinto del `TokenDeAcceso` (`api/auth.py`), vale solo para la versión a
la que se emite y caduca con `operation.session_timeout_seconds` (013-C06, 013-C07, 013-I2)."""

from __future__ import annotations

import datetime as dt

import jwt

AUDIENCE = "view_token"


class ViewTokenError(Exception):
    """Token de vista mal formado, manipulado, caducado o de otro uso (013-C07)."""


def create_view_token(version_id: int, secret: str, seconds: int, now: dt.datetime) -> str:
    payload = {
        "sub": str(version_id),
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(seconds=seconds)).timestamp()),
        "aud": AUDIENCE,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_view_token(token: str, secret: str, *, now: dt.datetime) -> int:
    """Devuelve el id de versión del `sub`; `ViewTokenError` ante cualquier causa (013-C07)."""
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience=AUDIENCE,
            options={"verify_exp": False, "require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError as exc:
        raise ViewTokenError(str(exc)) from exc

    if now.timestamp() >= payload["exp"]:
        raise ViewTokenError("token de vista caducado")
    try:
        return int(payload["sub"])
    except (TypeError, ValueError) as exc:
        raise ViewTokenError("sub inválido") from exc

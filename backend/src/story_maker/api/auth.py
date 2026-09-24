"""Registro, acceso y el TokenDeAcceso: JWT HS256 con exp, aud e iss (002-C01 a 002-C14)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable

import bcrypt
from fastapi import APIRouter, Request
from pydantic import BaseModel

from story_maker.store.session import unit_of_work
from story_maker.store.users import create_user

Clock = Callable[[], dt.datetime]


def utc_now() -> dt.datetime:
    """Reloj por defecto: aware en UTC, para que `exp`/`iat` no dependan del huso del host."""
    return dt.datetime.now(dt.UTC)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False  # más de 72 bytes (002-C09): credenciales inválidas, nunca 500


class RegisterRequest(BaseModel):
    email: str
    password: str


class RegisterResponse(BaseModel):
    id: int
    email: str


router = APIRouter()


@router.post("/api/auth/register", status_code=201, response_model=RegisterResponse)
def register(payload: RegisterRequest, request: Request) -> RegisterResponse:
    state = request.app.state
    email = normalize_email(payload.email)

    with unit_of_work(state.session_factory) as uow:
        user = create_user(
            uow,
            email=email,
            password_hash=hash_password(payload.password),
            created_at=state.clock().replace(tzinfo=None),
        )

    return RegisterResponse(id=user.id, email=email)

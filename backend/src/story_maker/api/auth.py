"""Registro, acceso y el TokenDeAcceso: JWT HS256 con exp, aud e iss (002-C01 a 002-C14)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable

import bcrypt
import jwt
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from story_maker.store.session import unit_of_work
from story_maker.store.users import create_user, get_user_by_email

ISSUER = "story-maker"
AUDIENCE = "access_token"

Clock = Callable[[], dt.datetime]


def utc_now() -> dt.datetime:
    """Reloj por defecto: aware en UTC, para que `exp`/`iat` no dependan del huso del host."""
    return dt.datetime.now(dt.UTC)


class AuthError(Exception):
    """Token mal formado, manipulado, caducado o de otro uso (002-C12, 002-C13)."""


def normalize_email(email: str) -> str:
    return email.strip().lower()


def is_valid_email(email: str) -> bool:
    if not email or len(email) > 254 or " " in email or "\t" in email:
        return False
    if email.count("@") != 1:
        return False
    local, domain = email.split("@")
    if not local or "." not in domain:
        return False
    return not (domain.startswith(".") or domain.endswith("."))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False  # más de 72 bytes (002-C09): credenciales inválidas, nunca 500


def create_access_token(user_id: int, secret: str, hours: int, now: dt.datetime) -> str:
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(hours=hours)).timestamp()),
        "aud": AUDIENCE,
        "iss": ISSUER,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token: str, secret: str, *, now: dt.datetime) -> int:
    """Devuelve el id de cliente del `sub`; `AuthError` ante cualquier causa de 002-C12/C13/C14."""
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience=AUDIENCE,
            issuer=ISSUER,
            options={"verify_exp": False, "require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError as exc:
        raise AuthError(str(exc)) from exc

    if now.timestamp() >= payload["exp"]:
        raise AuthError("token caducado")
    try:
        return int(payload["sub"])
    except (TypeError, ValueError) as exc:
        raise AuthError("sub inválido") from exc


class RegisterRequest(BaseModel):
    email: str
    password: str


class RegisterResponse(BaseModel):
    id: int
    email: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str


router = APIRouter()


@router.post("/api/auth/register", status_code=201, response_model=RegisterResponse)
def register(payload: RegisterRequest, request: Request) -> RegisterResponse:
    state = request.app.state
    email = normalize_email(payload.email)
    if not is_valid_email(email):
        raise HTTPException(status_code=422, detail="email inválido")

    with unit_of_work(state.session_factory) as uow:
        if get_user_by_email(uow.session, email) is not None:
            raise HTTPException(status_code=409, detail="email ya registrado")
        user = create_user(
            uow,
            email=email,
            password_hash=hash_password(payload.password),
            created_at=state.clock().replace(tzinfo=None),
        )

    return RegisterResponse(id=user.id, email=email)


@router.post("/api/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request) -> LoginResponse:
    state = request.app.state
    email = normalize_email(payload.email)
    session = state.session_factory()
    try:
        user = get_user_by_email(session, email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="credenciales inválidas")
        token = create_access_token(
            user.id, state.jwt_secret, state.access_token_hours, state.clock()
        )
    finally:
        session.close()

    return LoginResponse(access_token=token)

"""Repositorio de clientes: alta y búsqueda por email (002-C01 a 002-C03)."""

from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from story_maker.store.models import User
from story_maker.store.session import UnitOfWork


def get_user_by_email(session: Session, email: str) -> User | None:
    """`email` ya viene normalizado (minúsculas, sin espacios en los extremos)."""
    return session.query(User).filter(User.email == email).one_or_none()


def create_user(
    uow: UnitOfWork, *, email: str, password_hash: str, created_at: dt.datetime
) -> User:
    user = User(email=email, password_hash=password_hash, created_at=created_at)
    uow.add(user)
    return user

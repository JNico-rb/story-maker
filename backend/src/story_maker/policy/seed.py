"""Siembra la lista global de `banned_terms` desde `domain`, sin duplicar (architecture.md §12.1,
005-C18)."""

from sqlalchemy import select

from story_maker.domain.banned_terms import normalize_token
from story_maker.domain.global_banned_terms import GLOBAL_BANNED_TERMS
from story_maker.store.models import BannedTerm
from story_maker.store.session import UnitOfWork


def seed_global_banned_terms(uow: UnitOfWork) -> None:
    """Inserta una entrada `global`/`word` por término de `GLOBAL_BANNED_TERMS` que aún no
    exista, comparando por forma normalizada; una segunda siembra no añade nada."""
    existing = {
        row[0]
        for row in uow.session.execute(
            select(BannedTerm.normalized).where(BannedTerm.level == "global")
        )
    }
    for term in GLOBAL_BANNED_TERMS:
        normalized = normalize_token(term)
        if normalized in existing:
            continue
        uow.add(BannedTerm(level="global", term=term, type="word", normalized=normalized))
        existing.add(normalized)

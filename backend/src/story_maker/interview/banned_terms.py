"""Añadir una entrada a una lista de prohibidas: valida forma, normaliza y evita duplicados
(005 hace la coincidencia por tokens; 008 escribe, desde `update_brief` y desde las rutas de la
API — 008-C04, 008-C25, 008-C26)."""

from __future__ import annotations

from story_maker.domain.banned_terms import normalize_token, tokenize
from story_maker.store.models import BannedTerm
from story_maker.store.session import UnitOfWork


class InvalidBannedTerm(ValueError):
    """Término vacío, tema sin palabras clave o palabra con palabras clave (008-C25)."""


def normalized_term(term: str) -> str:
    return " ".join(normalize_token(token) for token in tokenize(term))


def add_banned_term(
    uow: UnitOfWork,
    *,
    level: str,
    user_id: int | None,
    novel_id: int | None,
    term: str,
    type_: str,
    keywords: list[str],
) -> BannedTerm | None:
    """Crea la entrada normalizada, o devuelve `None` si ya había una igual (mismo nivel, dueño,
    tipo y forma normalizada): dedup silencioso, como en el parche de `update_brief` (008-C04).
    Las rutas de la API distinguen ese `None` para responder 409 (008-C25, 008-C26)."""
    if not term.strip():
        raise InvalidBannedTerm("el término no puede estar vacío")
    if type_ == "topic" and not keywords:
        raise InvalidBannedTerm("un tema necesita al menos una palabra clave")
    if type_ == "word" and keywords:
        raise InvalidBannedTerm("una palabra no lleva palabras clave")

    normalized = normalized_term(term)
    existing = (
        uow.session.query(BannedTerm)
        .filter(
            BannedTerm.level == level,
            BannedTerm.user_id == user_id,
            BannedTerm.novel_id == novel_id,
            BannedTerm.type == type_,
            BannedTerm.normalized == normalized,
        )
        .one_or_none()
    )
    if existing is not None:
        return None

    row = BannedTerm(
        level=level,
        user_id=user_id,
        novel_id=novel_id,
        term=term,
        type=type_,
        keywords=keywords or None,
        normalized=normalized,
    )
    uow.add(row)
    return row

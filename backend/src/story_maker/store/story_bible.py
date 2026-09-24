"""Story bible de una versión: el cambio del valor de un hecho en una candidata (009-C15, 009-C16)
y las lecturas de la story bible y de su cronología registrada (009-C23, 009-C24)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from story_maker.store.brief_canon import NAME
from story_maker.store.models import Character, Fact
from story_maker.store.session import UnitOfWork


def change_fact_value(uow: UnitOfWork, fact_id: int, value: str) -> Fact:
    """Cambia el valor del hecho `fact_id` en su versión (solo una candidata lo admite). Si es el
    hecho de nombre de un personaje, su nombre canónico cambia con él, en la misma transacción
    (`definitions.md` §2 Personaje). Lo usan 014 y 019 (009-I8)."""
    fact = _fact(uow.session, fact_id)
    fact.value = value
    if fact.attribute == NAME and fact.character_id is not None:
        _rename_character(uow.session, fact.character_id, value)
    return fact


def _rename_character(session: Session, character_id: int, name: str) -> None:
    character = session.get(Character, character_id)
    if character is None:
        raise LookupError(f"no existe el personaje {character_id}")
    character.canonical_name = name


def _fact(session: Session, fact_id: int) -> Fact:
    fact = session.get(Fact, fact_id)
    if fact is None:
        raise LookupError(f"no existe el hecho {fact_id}")
    return fact

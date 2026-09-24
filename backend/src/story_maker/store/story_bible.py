"""Story bible de una versión: el cambio del valor de un hecho en una candidata (009-C15, 009-C16)
y las lecturas de la story bible y de su cronología registrada (009-C23, 009-C24)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from story_maker.store.models import Fact
from story_maker.store.session import UnitOfWork


def change_fact_value(uow: UnitOfWork, fact_id: int, value: str) -> Fact:
    """Cambia el valor del hecho `fact_id` en su versión (solo una candidata lo admite)."""
    fact = _fact(uow.session, fact_id)
    fact.value = value
    return fact


def _fact(session: Session, fact_id: int) -> Fact:
    fact = session.get(Fact, fact_id)
    if fact is None:
        raise LookupError(f"no existe el hecho {fact_id}")
    return fact

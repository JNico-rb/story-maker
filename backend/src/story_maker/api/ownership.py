"""Un recurso de otro cliente responde como inexistente (002-C16 a 002-C21, I3)."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import HTTPException
from sqlalchemy.orm import Session

NOT_FOUND_DETAIL = "no encontrado"


def owned_or_404[T](
    session: Session, model: type[T], resource_id: object, is_owned: Callable[[T], bool]
) -> T:
    """Busca `model` por `resource_id`; si no existe o `is_owned` la rechaza, 404, idéntico al de
    un id inexistente (002-C16, 002-C17, 002-C18)."""
    obj = session.get(model, resource_id)
    if obj is None or not is_owned(obj):
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    return obj

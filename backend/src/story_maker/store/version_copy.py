"""Copia de versión: la candidata de un cambio o de una edición nace como copia íntegra de su base,
en una transacción y compartiendo los vectores (`architecture.md` §9.3, §6.4; 009-C11 a 009-C14).
"""

from __future__ import annotations

import copy
import datetime as dt
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from story_maker.store.models import (
    Base,
    CanonCard,
    Chapter,
    Character,
    Event,
    EventCharacter,
    Fact,
    FactUsage,
    OutlineChapter,
    Place,
    StyleSheet,
    Version,
    World,
)
from story_maker.store.session import UnitOfWork

# Tablas de ámbito versión (§15.6), en un orden en el que cada una solo apunta a las anteriores.
VERSION_TABLES: tuple[type[Base], ...] = (
    World,
    Character,
    Place,
    Fact,
    FactUsage,
    Event,
    EventCharacter,
    OutlineChapter,
    StyleSheet,
    Chapter,
    CanonCard,
)

# Referencias internas: columna → tabla a la que apunta, dentro de la misma versión (009-I2).
REFERENCES: dict[type[Base], dict[str, str]] = {
    Fact: {"character_id": "characters", "place_id": "places"},
    FactUsage: {"fact_id": "facts"},
    Event: {"place_id": "places", "excluded_character_id": "characters"},
    EventCharacter: {"event_id": "events", "character_id": "characters"},
    CanonCard: {"character_id": "characters", "place_id": "places"},
}


@dataclass(frozen=True)
class VersionCopy:
    """La candidata y la traducción completa de sus ids: tabla → id en la base → id en la
    candidata (`architecture.md` §18, «Identidad de una entidad de ámbito versión al copiar»)."""

    version: Version
    ids: Mapping[str, Mapping[int, int]]


def copy_version(uow: UnitOfWork, base_id: int, *, now: dt.datetime) -> VersionCopy:
    """Copia la versión `base_id` en una candidata nueva dentro de la transacción de `uow`. Cada
    fila nace con un id propio y toda referencia interna apunta a la fila nueva. Las CanonCards
    entran en el canal léxico al confirmar la unidad de trabajo; los vectores no se tocan: se
    comparten por huella y modelo (§6.3)."""
    base = uow.session.get(Version, base_id)
    if base is None:
        raise LookupError(f"no existe la versión {base_id}")
    candidate = Version(
        novel_id=base.novel_id,
        status="candidate",
        base_version_id=base.id,
        changed_chapters=[],
        created_at=now,
    )
    uow.add(candidate)
    uow.session.flush()
    ids: dict[str, dict[int, int]] = {}
    for model in VERSION_TABLES:
        ids[model.__tablename__] = _copy_table(uow, model, base.id, candidate.id, ids)
    return VersionCopy(candidate, ids)


def rows_of_version(session: Session, model: type[Base], version_id: int) -> list[Any]:
    """Las filas de `model` en la versión; `fact_usages` y `event_characters` cuelgan de su hecho
    y de su evento."""
    query = session.query(model)
    if model is FactUsage:
        query = query.join(Fact, Fact.id == FactUsage.fact_id).filter(Fact.version_id == version_id)
    elif model is EventCharacter:
        query = query.join(Event, Event.id == EventCharacter.event_id).filter(
            Event.version_id == version_id
        )
    else:
        query = query.filter(model.version_id == version_id)  # type: ignore[attr-defined]
    return list(query.order_by(model.id).all())  # type: ignore[attr-defined]


def _copy_table(
    uow: UnitOfWork,
    model: type[Base],
    base_id: int,
    candidate_id: int,
    ids: dict[str, dict[int, int]],
) -> dict[int, int]:
    references = REFERENCES.get(model, {})
    columns = [attr.key for attr in inspect(model).column_attrs if attr.key != "id"]
    pairs = []
    for row in rows_of_version(uow.session, model, base_id):
        values = {column: copy.deepcopy(getattr(row, column)) for column in columns}
        if "version_id" in values:
            values["version_id"] = candidate_id
        for column, target in references.items():
            if values[column] is not None:
                values[column] = ids[target][values[column]]
        new_row = model(**values)
        uow.add(new_row)
        pairs.append((row.id, new_row))
    uow.session.flush()
    return {old_id: new_row.id for old_id, new_row in pairs}  # type: ignore[attr-defined]

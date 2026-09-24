"""Escritura de la fila de `chronology_files` para 007-validador-lean: la huella del fichero, el
resultado y su detalle. Cuándo se escribe y con qué contenido lo fija y lo prueba la 007 (007-C09 a
007-C12, 007-I12); aquí solo nace la escritura (spec 009, alcance)."""

from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from story_maker.store.models import ChronologyFile
from story_maker.store.session import UnitOfWork

ChronologyFileResult = Literal["passed", "failed", "error"]


def record_chronology_file(
    uow: UnitOfWork,
    *,
    run_id: int,
    content_hash: str,
    result: ChronologyFileResult,
    detail: dict[str, Any] | list[Any] | None,
    now: dt.datetime,
) -> ChronologyFile:
    row = ChronologyFile(
        run_id=run_id, content_hash=content_hash, result=result, detail=detail, created_at=now
    )
    uow.add(row)
    uow.session.flush()
    return row

"""Capítulos afectados por una propuesta, calculados por el código desde la versión base: los
`UsoDeHecho` de los hechos cambiados, más los capítulos con el valor antiguo literal
(`architecture.md` §10.1 paso 4; 014-I1)."""

from __future__ import annotations

import re
from collections.abc import Iterable

from sqlalchemy.orm import Session

from story_maker.store.models import Chapter, FactUsage


def affected_chapters(
    session: Session, version_id: int, changes: Iterable[tuple[int, str]]
) -> list[int]:
    """`changes` son pares (hecho, valor antiguo) de la versión base."""
    chapters = session.query(Chapter).filter(Chapter.version_id == version_id).all()
    affected: set[int] = set()
    for fact_id, old_value in changes:
        usages = session.query(FactUsage.chapter).filter(FactUsage.fact_id == fact_id)
        affected.update(chapter for (chapter,) in usages)
        affected.update(c.number for c in chapters if _contains(c.text, old_value))
    return sorted(affected)


def _contains(text: str, value: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(value)}(?!\w)", text) is not None

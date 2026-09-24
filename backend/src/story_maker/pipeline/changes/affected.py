"""Capítulos afectados por una propuesta, calculados por el código desde la versión base: los
`UsoDeHecho` de los hechos cambiados, más los capítulos con el valor antiguo literal en su título
o su texto, más el capítulo del fragmento (`architecture.md` §10.1 paso 4; 014-C02, 014-I1)."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from sqlalchemy.orm import Session

from story_maker.store.models import Chapter, FactUsage

_WORD = re.compile(r"\w+")


def affected_chapters(
    session: Session,
    version_id: int,
    changes: Iterable[tuple[int, str]],
    fragment_chapter: int | None = None,
) -> list[int]:
    """`changes` son pares (hecho, valor antiguo) de la versión base."""
    chapters = session.query(Chapter).filter(Chapter.version_id == version_id).all()
    affected: set[int] = set() if fragment_chapter is None else {fragment_chapter}
    for fact_id, old_value in changes:
        usages = session.query(FactUsage.chapter).filter(FactUsage.fact_id == fact_id)
        affected.update(chapter for (chapter,) in usages)
        needle = _words(old_value)
        affected.update(
            c.number for c in chapters if _contains(_words(f"{c.title}\n{c.text}"), needle)
        )
    return sorted(affected)


def _words(text: str) -> list[str]:
    """Palabras sin mayúsculas ni acentos: así la búsqueda colapsa los espacios y va por
    palabras completas."""
    folded = unicodedata.normalize("NFD", text.lower())
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    return _WORD.findall(folded)


def _contains(words: list[str], needle: list[str]) -> bool:
    width = len(needle)
    if width == 0:
        return False
    return any(words[i : i + width] == needle for i in range(len(words) - width + 1))

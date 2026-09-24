"""Canal léxico: palabras, candidatos de FTS5 y BM25 en código (`architecture.md` §6.3)."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Collection

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

_WORD = re.compile(r"[^\W_]+")

_CANDIDATES = text(
    "SELECT rowid FROM canon_cards_fts WHERE canon_cards_fts MATCH :match AND rowid IN :ids"
).bindparams(bindparam("ids", expanding=True))


def words(value: str) -> list[str]:
    """Las palabras de `value`: secuencias de letras y dígitos, sin mayúsculas ni diacríticos,
    como el tokenizador `unicode61 remove_diacritics 2` del índice."""
    decomposed = unicodedata.normalize("NFD", value)
    bare = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return _WORD.findall(bare.lower())


def candidates(
    session: Session, query_words: Collection[str], card_ids: Collection[int]
) -> set[int]:
    """Las tarjetas de `card_ids` que comparten al menos una palabra con la consulta. Cada
    palabra va entre comillas: FTS5 la busca como palabra y nunca como operador."""
    if not query_words or not card_ids:
        return set()
    match = " OR ".join(f'"{word}"' for word in sorted(query_words))
    rows = session.execute(_CANDIDATES, {"match": match, "ids": list(card_ids)})
    return {row[0] for row in rows}

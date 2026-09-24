"""Canal léxico: palabras, candidatos de FTS5 y BM25 en código (`architecture.md` §6.3)."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from collections.abc import Collection, Mapping

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

_WORD = re.compile(r"[^\W_]+")

K1 = 1.2
B = 0.75

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


def bm25(
    query_words: Collection[str], eligible: Mapping[int, str], scored: Collection[int]
) -> dict[int, float]:
    """BM25 de las tarjetas `scored`, con N, df y la longitud media de las `eligible` (id → texto)
    y cada palabra distinta de la consulta una vez."""
    if not scored:
        return {}
    counts = {card_id: Counter(words(body)) for card_id, body in eligible.items()}
    n = len(counts)
    average = sum(c.total() for c in counts.values()) / n
    idf: dict[str, float] = {}
    for word in sorted(query_words):
        df = sum(1 for c in counts.values() if word in c)
        idf[word] = math.log(1 + (n - df + 0.5) / (df + 0.5))
    scores: dict[int, float] = {}
    for card_id in scored:
        tf, length = counts[card_id], counts[card_id].total()
        norm = K1 * (1 - B + B * length / average)
        scores[card_id] = sum(idf[word] * tf[word] * (K1 + 1) / (tf[word] + norm) for word in idf)
    return scores

"""Las comprobaciones que el lint en vivo marca como bloqueantes y que el guardado rechaza: las
mismas funciones en las dos rutas, así que lo que avisa el lint es lo que bloquea (019-I3)."""

from __future__ import annotations

import re
from collections.abc import Sequence

from sqlalchemy.orm import Session

from story_maker.domain.banned_terms import find_term_matches, tokenize
from story_maker.pipeline.manual_edit.diagnostics import Diagnostic
from story_maker.pipeline.planning.session import _active_banned_entries
from story_maker.policy.types import EntradaProhibida, PeticionDePolitica
from story_maker.validators.exact_names import name_variants

_LETTERS = re.compile(r"[^\W\d_]+")
_TOKEN = re.compile(r"\w+")


def name_variant_diagnostics(text: str, canonical_names: Sequence[str]) -> list[Diagnostic]:
    """Cada forma no canónica de un nombre, con su posición; qué es variante lo fija
    `nombres-exactos` (011)."""
    found = []
    for match in _LETTERS.finditer(text):
        for variant in name_variants("", match.group(0), canonical_names):
            found.append(
                Diagnostic(
                    "forma_no_canonica",
                    variant.message,
                    blocking=True,
                    start=match.start(),
                    end=match.end(),
                    extra={"variant": variant.word, "canonical": variant.canonical},
                )
            )
    return found


def active_banned(session: Session, user_id: int, novel_id: int) -> list[EntradaProhibida]:
    """Las prohibidas de los tres niveles que aplican: global, las del cliente y las de la novela
    (005)."""
    peticion = PeticionDePolitica(origen="manual_edit", cliente=str(user_id), novela=str(novel_id))
    return _active_banned_entries(session, peticion)


def banned_diagnostics(text: str, entries: Sequence[EntradaProhibida]) -> list[Diagnostic]:
    """Cada coincidencia de una prohibida, con la normalización de 005 y su posición: por tokens
    completos, sobre cada tramo de tantos tokens como el término."""
    tokens = list(_TOKEN.finditer(text))
    found = []
    for entry in entries:
        needles = entry.keywords if entry.type == "topic" else [entry.term]
        for needle in needles:
            width = len(tokenize(needle))
            for i in range(len(tokens) - width + 1) if width else ():
                start, end = tokens[i].start(), tokens[i + width - 1].end()
                matches = find_term_matches(text[start:end], needle)
                if not matches:
                    continue
                found.append(
                    Diagnostic(
                        "prohibida",
                        f"«{matches[0]}» es una prohibida de nivel {entry.level} («{entry.term}»)",
                        blocking=True,
                        start=start,
                        end=end,
                        extra={"term": entry.term, "level": entry.level, "variant": matches[0]},
                    )
                )
    return found

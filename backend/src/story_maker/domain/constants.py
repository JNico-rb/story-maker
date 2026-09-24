"""Constantes del encargo e identificadores que valida la config (`definitions.md` §11.2, §12.2)."""

from __future__ import annotations

CHAPTERS_PER_NOVEL = 10
MIN_WORDS_PER_CHAPTER = 1000
MAX_WORDS_PER_CHAPTER = 1500
TOKEN_CEILING_MAX = 100000

ROLES = ("interviewer", "extractor", "planner", "writer", "editor", "judge", "visual_reviewer")

CRITERIA = (
    "fidelidad-canon",
    "cumple-beats",
    "personalizacion-natural",
    "prosa",
    "tono",
    "continuidad",
    "coherencia-personajes",
    "arco-y-final",
    "ritmo",
    "no-cliche",
)

AGE_BANDS = ("children", "teen", "adult")

# Del plan y del outline (010; `definitions.md` §11.2).
MIN_CONSEQUENCES = 2
MAX_CONSEQUENCES = 4
MIN_BEATS = 3
MAX_BEATS = 6

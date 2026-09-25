"""`nombres-exactos`: los personajes se escriben exactamente como en la story bible
(`architecture.md` §11.2; 011-C12). Corre en el hook de validación de capítulo y, en 012, sobre
la novela."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from story_maker.agents.port import Defect
from story_maker.validators.chapter_check import ChapterCheck

EXACT_NAMES = "nombres-exactos"

_LETTERS = re.compile(r"[^\W\d_]+")


@dataclass(frozen=True)
class NameVariant:
    word: str
    canonical: str

    @property
    def message(self) -> str:
        return f"«{self.word}» es una variante de «{self.canonical}»"


def letter_words(text: str) -> list[str]:
    """Tramos de letras: «¿Toby?» es «Toby»."""
    return _LETTERS.findall(text)


def _fold(word: str) -> str:
    """Sin mayúsculas ni acentos."""
    decomposed = unicodedata.normalize("NFD", word.lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _allowed_distance(canonical: str) -> int:
    letters = len(canonical)
    if letters >= 7:
        return 2
    if letters >= 4:
        return 1
    return 0


def edit_distance(a: str, b: str) -> int:
    """Inserciones, borrados y sustituciones de una letra (Levenshtein)."""
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            current.append(
                min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (char_a != char_b))
            )
        previous = current
    return previous[-1]


def _capitalized(words: Iterable[str]) -> list[str]:
    return [word for word in words if word[0].isupper()]


def _lowercase_folded_words(*texts: str) -> set[str]:
    """Palabras del título o del texto que empiezan por minúscula, sin mayúsculas ni acentos."""
    return {_fold(word) for text in texts for word in letter_words(text) if word[0].islower()}


def name_variants(title: str, text: str, canonical_names: Sequence[str]) -> list[NameVariant]:
    """Cada palabra con mayúscula inicial del título y del texto que no es ya una palabra de un
    nombre canónico, que el mismo título o texto no escribe también empezando por minúscula (una
    palabra corriente a principio de frase), y que es variante de mayúsculas o acentos, o está a la
    distancia admitida, de una palabra con mayúscula de un nombre canónico; las partículas («de»)
    no se comparan."""
    canonical_words = [word for name in canonical_names for word in letter_words(name)]
    exact = set(canonical_words)
    comparable = list(dict.fromkeys(_capitalized(canonical_words)))
    lowercase_elsewhere = _lowercase_folded_words(title, text)
    variants: list[NameVariant] = []
    for word in _capitalized(letter_words(title) + letter_words(text)):
        if word in exact:
            continue
        folded = _fold(word)
        if folded in lowercase_elsewhere:
            continue
        for canonical in comparable:
            target = _fold(canonical)
            if folded == target or edit_distance(folded, target) <= _allowed_distance(target):
                variants.append(NameVariant(word, canonical))
                break
    return variants


def check_exact_names(title: str, text: str, canonical_names: Sequence[str]) -> ChapterCheck:
    variants = name_variants(title, text, canonical_names)
    defects = tuple(Defect(EXACT_NAMES, v.message, blocking=True) for v in variants)
    comment = "; ".join(v.message for v in variants) or "sin variantes"
    return ChapterCheck(EXACT_NAMES, passed=not variants, comment=comment, defects=defects)

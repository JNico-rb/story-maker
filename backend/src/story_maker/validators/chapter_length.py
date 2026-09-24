"""`longitud-capitulo`: el texto de un capítulo tiene de 1.000 a 1.500 palabras (`architecture.md`
§11.2; 011-C11)."""

from __future__ import annotations

from story_maker.agents.port import Defect
from story_maker.domain.constants import MAX_WORDS_PER_CHAPTER, MIN_WORDS_PER_CHAPTER
from story_maker.validators.chapter_check import ChapterCheck

LENGTH = "longitud-capitulo"


def words(text: str) -> list[str]:
    """Las palabras de `text`: cada tramo sin espacios que contiene una letra o un dígito, así que
    una raya o unos puntos suspensivos sueltos no cuentan (§18, spec 011)."""
    return [token for token in text.split() if any(char.isalnum() for char in token)]


def count_words(text: str) -> int:
    return len(words(text))


def _thousands(number: int) -> str:
    return f"{number:,}".replace(",", ".")


def check_chapter_length(text: str) -> ChapterCheck:
    """El título no cuenta: solo el texto."""
    counted = count_words(text)
    comment = f"{counted} palabras"
    if MIN_WORDS_PER_CHAPTER <= counted <= MAX_WORDS_PER_CHAPTER:
        return ChapterCheck(LENGTH, passed=True, comment=comment)
    message = (
        f"el capítulo tiene {_thousands(counted)} palabras; el rango es "
        f"de {_thousands(MIN_WORDS_PER_CHAPTER)} a {_thousands(MAX_WORDS_PER_CHAPTER)}"
    )
    return ChapterCheck(
        LENGTH, passed=False, comment=comment, defects=(Defect(LENGTH, message, blocking=True),)
    )

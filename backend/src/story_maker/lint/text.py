"""Utilidades de texto compartidas por los cuatro linters (`Reglas comunes`, spec 018)."""

from __future__ import annotations

import re

#: Una palabra: solo sus letras, con tilde, ñ y ü (`Reglas comunes`, «Palabra»).
WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+")

#: Un párrafo es un bloque separado del siguiente por una línea en blanco.
_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")

#: Signos finales de frase (`Reglas comunes`, «Frase»); ¡ y ¿ no son signos finales.
_FINAL_CHARS = ".!?…"

#: Vocales de una palabra (`Reglas comunes`, «Sílabas»).
_VOWELS = "aeiouáéíóúü"


def split_paragraphs(text: str) -> list[str]:
    """Los párrafos de `text`, en orden; un párrafo vacío no cuenta."""
    return [block for block in _PARAGRAPH_SPLIT_RE.split(text.strip()) if block.strip()]


def extract_words(text: str) -> list[str]:
    """Las palabras de `text`, tal como aparecen (sin tocar mayúsculas ni tildes)."""
    return WORD_RE.findall(text)


def comparison_form(word: str) -> str:
    """Forma de comparación de `word`: minúsculas, tildes intactas (`Reglas comunes`,
    «Comparación»: no distingue mayúsculas, pero sí tildes)."""
    return word.lower()


def find_sequences(words: list[str], phrase: str) -> list[int]:
    """Índices de inicio donde `phrase` (una o varias palabras) aparece en `words` como
    palabras completas y consecutivas (`Reglas comunes`, «Comparación»)."""
    phrase_words = [comparison_form(word) for word in extract_words(phrase)]
    if not phrase_words:
        return []
    normalized = [comparison_form(word) for word in words]
    width = len(phrase_words)
    return [
        start
        for start in range(len(words) - width + 1)
        if normalized[start : start + width] == phrase_words
    ]


def _is_vowel(char: str, index: int, length: int) -> bool:
    lower = char.lower()
    if lower in _VOWELS:
        return True
    return lower == "y" and index == length - 1


def count_syllables(word: str) -> int:
    """Núcleos vocálicos de `word` (`Reglas comunes`, «Sílabas»)."""
    length = len(word)
    runs = 0
    previous_was_vowel = False
    for index, char in enumerate(word):
        is_vowel = _is_vowel(char, index, length)
        if is_vowel and not previous_was_vowel:
            runs += 1
        previous_was_vowel = is_vowel
    return runs


def count_sentences(paragraph: str) -> int:
    """Frases de un párrafo (`Reglas comunes`, «Frase»): un párrafo sin signo final cierra
    su última frase."""
    count = 0
    length = len(paragraph)
    index = 0
    last_cut = 0
    while index < length:
        if paragraph[index] in _FINAL_CHARS:
            end = index
            while end < length and paragraph[end] in _FINAL_CHARS:
                end += 1
            count += 1
            last_cut = end
            index = end
        else:
            index += 1
    if paragraph[last_cut:].strip():
        count += 1
    return count

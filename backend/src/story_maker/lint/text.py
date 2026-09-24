"""Utilidades de texto compartidas por los cuatro linters (`Reglas comunes`, spec 018)."""

from __future__ import annotations

import re

#: Una palabra: solo sus letras, con tilde, ñ y ü (`Reglas comunes`, «Palabra»).
WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+")

#: Un párrafo es un bloque separado del siguiente por una línea en blanco.
_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")

#: Signos finales de frase (`Reglas comunes`, «Frase»); ¡ y ¿ no son signos finales.
_FINAL_CHARS = ".!?…"

#: Vocales fuertes, sin y con tilde (`Reglas comunes`, «Sílabas»).
_STRONG_VOWELS = "aeoáéó"

#: Vocales débiles, sin y con tilde, y ü (`Reglas comunes`, «Sílabas»).
_WEAK_VOWELS = "iuíúü"

#: Vocales con tilde: solo í y ú separan de una fuerte vecina (`Reglas comunes`, «Sílabas»).
_ACCENTED_WEAK_VOWELS = "íú"


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


def _vowel_kind(char: str, index: int, length: int) -> tuple[bool, bool] | None:
    """`(fuerte, con_tilde)` si `char` es vocal en esa posición, si no `None`."""
    lower = char.lower()
    if lower in _STRONG_VOWELS:
        return True, lower not in "aeo"
    if lower in _WEAK_VOWELS:
        return False, lower in _ACCENTED_WEAK_VOWELS
    if lower == "y" and index == length - 1:
        return False, False
    return None


def _splits_hiatus(previous: tuple[bool, bool], current: tuple[bool, bool]) -> bool:
    """Entre dos vocales fuertes, o entre una débil con tilde y una fuerte vecina
    (`Reglas comunes`, «Sílabas»)."""
    previous_strong, previous_accented = previous
    current_strong, current_accented = current
    if previous_strong and current_strong:
        return True
    previous_is_accented_weak = not previous_strong and previous_accented
    current_is_accented_weak = not current_strong and current_accented
    return (previous_is_accented_weak and current_strong) or (
        current_is_accented_weak and previous_strong
    )


def count_syllables(word: str) -> int:
    """Núcleos vocálicos de `word` (`Reglas comunes`, «Sílabas»): una serie de vocales es
    un solo núcleo, salvo hiato entre dos fuertes o entre una débil con tilde y una fuerte."""
    length = len(word)
    nuclei = 0
    previous_vowel: tuple[bool, bool] | None = None
    for index, char in enumerate(word):
        vowel = _vowel_kind(char, index, length)
        if vowel is None:
            previous_vowel = None
            continue
        if previous_vowel is None or _splits_hiatus(previous_vowel, vowel):
            nuclei += 1
        previous_vowel = vowel
    return nuclei


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

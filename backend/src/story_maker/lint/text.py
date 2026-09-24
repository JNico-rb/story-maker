"""Utilidades de texto compartidas por los cuatro linters (`Reglas comunes`, spec 018)."""

from __future__ import annotations

import re

#: Una palabra: solo sus letras, con tilde, ñ y ü (`Reglas comunes`, «Palabra»).
WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+")

#: Un párrafo es un bloque separado del siguiente por una línea en blanco.
_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")


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

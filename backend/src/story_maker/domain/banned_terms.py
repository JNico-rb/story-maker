"""Normalización y coincidencia por tokens de términos prohibidos (architecture.md §12.1)."""

import re
import unicodedata

_LEETSPEAK = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "@": "a", "5": "s"})
_REPEATED_LETTERS = re.compile(r"(.)\1+")
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def normalize_token(token: str) -> str:
    """Forma normalizada de un token: minúsculas, sin acentos, sin leetspeak simple,
    sin letras repetidas y sin el plural en -s. Idempotente (005-I3)."""
    text = token.lower().translate(_LEETSPEAK)
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = _REPEATED_LETTERS.sub(r"\1", text)
    if text.endswith("s"):
        text = text[:-1]
    return text


def tokenize(text: str) -> list[str]:
    """Tokens de `text`, con límites de palabra (unicode-aware)."""
    return _TOKEN_RE.findall(text)


def find_term_matches(text: str, term: str) -> list[str]:
    """Apariciones de `term` (una o varias palabras) en `text`, en forma normalizada
    y por tokens completos; devuelve las variantes tal como aparecieron."""
    term_tokens = [normalize_token(token) for token in tokenize(term)]
    if not term_tokens:
        return []
    text_tokens = tokenize(text)
    normalized_text_tokens = [normalize_token(token) for token in text_tokens]
    width = len(term_tokens)
    matches = []
    for start in range(len(text_tokens) - width + 1):
        window = normalized_text_tokens[start : start + width]
        if window == term_tokens:
            matches.append(" ".join(text_tokens[start : start + width]))
    return matches

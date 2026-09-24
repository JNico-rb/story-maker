"""Normalización y coincidencia por tokens de términos prohibidos (architecture.md §12.1)."""

import re
import unicodedata

_LEETSPEAK = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "@": "a", "5": "s"})
_REPEATED_LETTERS = re.compile(r"(.)\1+")
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_VOWELS = set("aeiou")


def _base_form(token: str) -> str:
    """Minúsculas, sin acentos, sin leetspeak simple y con las letras repetidas colapsadas;
    sin tocar el plural (lo hace `normalize_token`, que reduce solo el de -s)."""
    text = token.lower().translate(_LEETSPEAK)
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return _REPEATED_LETTERS.sub(r"\1", text)


def normalize_token(token: str) -> str:
    """Forma normalizada de un token: `_base_form` sin el plural en -s. Idempotente (005-I3).

    Quitar solo una «s» final es una operación limpia (añadir «s» y luego quitarla siempre
    deshace el cambio, para cualquier palabra). El plural en -es no se reduce aquí: un radical
    que ya acaba en consonante+«e» en singular («parte», «coche») es indistinguible, por la
    forma, de un radical consonántico con «es» añadido («amor» → «amores»); `find_term_matches`
    lo reconoce aparte, comparando contra el término conocido en vez de adivinar el radical del
    texto (hallazgo del verificador, 005-I3)."""
    text = _base_form(token)
    if text.endswith("s"):
        text = text[:-1]
    return text


def tokenize(text: str) -> list[str]:
    """Tokens de `text`, con límites de palabra (unicode-aware)."""
    return _TOKEN_RE.findall(text)


def _matches_es_plural(text_token: str, term_normalized: str) -> bool:
    """`text_token` es el plural en -es de `term_normalized`: el plural en -es solo existe para
    un radical de al menos 3 letras que acaba en consonante distinta de «s» (arq. §12.1); un
    radical que acaba en vocal o en «s» pluraliza en -s, ya cubierto por `normalize_token`."""
    if len(term_normalized) < 3 or term_normalized[-1] in _VOWELS or term_normalized[-1] == "s":
        return False
    return _base_form(text_token) == term_normalized + "es"


def find_term_matches(text: str, term: str) -> list[str]:
    """Apariciones de `term` (una o varias palabras) en `text`, en forma normalizada
    y por tokens completos; devuelve las variantes tal como aparecieron. Para un término de un
    solo token, también cuenta su plural en -es (005-I3)."""
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
        elif width == 1 and _matches_es_plural(text_tokens[start], term_tokens[0]):
            matches.append(text_tokens[start])
    return matches

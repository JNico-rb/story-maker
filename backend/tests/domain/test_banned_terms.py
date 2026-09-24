"""Normalización y coincidencia por tokens de términos prohibidos (architecture.md §12.1)."""

from hypothesis import given
from hypothesis import strategies as st

from story_maker.domain.banned_terms import find_term_matches, normalize_token

_LOWERCASE_WORDS = st.text(alphabet="abcdefghijklmnopqrstuvwxyzáéíóúñ", min_size=1, max_size=12)


@given(_LOWERCASE_WORDS)
def test_normalizacion_es_idempotente(word: str) -> None:
    once = normalize_token(word)
    assert normalize_token(once) == once


@given(_LOWERCASE_WORDS)
def test_variantes_de_mayusculas_acento_plural_y_letras_repetidas_coinciden(word: str) -> None:
    variants = [
        word.upper(),
        word + "s",
        word[0] + word[0] + word[1:] if word else word,
    ]
    for variant in variants:
        assert find_term_matches(variant, word) == [variant]


@given(_LOWERCASE_WORDS, _LOWERCASE_WORDS)
def test_un_termino_nunca_coincide_dentro_de_otra_palabra(word: str, extra: str) -> None:
    if normalize_token(word) == normalize_token(word + extra):
        return
    assert find_term_matches(word + extra, word) == []


def test_una_variante_de_acento_coincide() -> None:
    assert find_term_matches("MÁRTA", "marta") == ["MÁRTA"]


def test_una_variante_de_plural_coincide() -> None:
    assert find_term_matches("las martas", "marta") == ["martas"]


def test_letras_repetidas_y_leetspeak_simple_coinciden() -> None:
    assert find_term_matches("maaarta", "marta") == ["maaarta"]
    assert find_term_matches("m4rt4", "marta") == ["m4rt4"]


def test_la_coincidencia_va_por_tokens_no_por_subcadena() -> None:
    assert find_term_matches("examen", "ex") == []
    assert find_term_matches("ex pareja", "ex") == ["ex"]
    assert find_term_matches("mañana", "ana") == []
    assert find_term_matches("banana", "ana") == []
    assert find_term_matches("Ana llegó", "ana") == ["Ana"]


def test_un_tema_coincide_por_cualquiera_de_sus_palabras_clave() -> None:
    keywords = ["separación", "custodia"]
    assert any(find_term_matches("hablaron de la separación", k) for k in keywords)
    assert any(find_term_matches("pidió la custodia", k) for k in keywords)
    assert not any(find_term_matches("se fueron de viaje", k) for k in keywords)

"""Normalización y coincidencia por tokens de términos prohibidos (architecture.md §12.1)."""

from story_maker.domain.banned_terms import find_term_matches


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

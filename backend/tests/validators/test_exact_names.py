"""`nombres-exactos` sobre el título y el texto (011-C12; `verification.md` §5 5a.2, §6 U10)."""

from __future__ import annotations

import pytest

from story_maker.validators.exact_names import EXACT_NAMES, check_exact_names

CANONICAL = ("Toby", "Nala", "Nela", "Ana", "Bernabé", "Marta López")


@pytest.mark.parametrize(
    ("word", "canonical"),
    [
        ("TOBY", "Toby"),
        ("Tóby", "Toby"),
        ("Tomy", "Toby"),
        ("Nada", "Nala"),
        ("ANA", "Ana"),
        ("Vernave", "Bernabé"),
        ("Lopez", "López"),
    ],
)
def test_a_variant_of_a_canonical_name_is_a_blocking_defect(word: str, canonical: str) -> None:
    check = check_exact_names("El faro", f"Aquella tarde vino {word} al puerto.", CANONICAL)

    assert check.validator == EXACT_NAMES
    assert check.passed is False
    assert len(check.defects) == 1
    defect = check.defects[0]
    assert defect.validator == EXACT_NAMES
    assert defect.blocking is True
    assert f"«{word}»" in defect.message
    assert f"«{canonical}»" in defect.message


@pytest.mark.parametrize(
    "word", ["Toby", "toby", "Tomi", "Nela", "Ane", "Bernardo", "Marta", "López", "¿Toby?"]
)
def test_canonical_names_lowercase_words_and_distant_words_pass(word: str) -> None:
    check = check_exact_names("El faro", f"Aquella tarde vino {word} al puerto.", CANONICAL)

    assert check.passed is True
    assert check.defects == ()


def test_a_word_is_a_run_of_letters() -> None:
    check = check_exact_names("El faro", "—¿Tobi? —preguntó.", CANONICAL)

    assert [d.message for d in check.defects] == ["«Tobi» es una variante de «Toby»"]


def test_the_title_is_also_checked() -> None:
    check = check_exact_names("El faro de Tobi", "Aquella tarde vino Toby.", CANONICAL)

    assert check.passed is False
    assert [d.message for d in check.defects] == ["«Tobi» es una variante de «Toby»"]

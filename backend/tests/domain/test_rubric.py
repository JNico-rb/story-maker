"""`Rubrica` de novela: constante del dominio con sus siete criterios (012-C25;
`architecture.md` §11.3)."""

from __future__ import annotations

from story_maker.domain.rubric import NOVEL_RUBRIC

BLOCKING = {"continuidad", "coherencia-personajes", "arco-y-final"}
NON_BLOCKING = {"ritmo", "tono", "personalizacion-natural", "no-cliche"}


def test_the_rubric_has_exactly_seven_criteria_with_no_repeated_names() -> None:
    names = [c.name for c in NOVEL_RUBRIC]

    assert len(names) == 7
    assert len(set(names)) == 7
    assert set(names) == BLOCKING | NON_BLOCKING


def test_exactly_the_first_three_criteria_are_blocking() -> None:
    blocking_names = {c.name for c in NOVEL_RUBRIC if c.blocking}
    non_blocking_names = {c.name for c in NOVEL_RUBRIC if not c.blocking}

    assert blocking_names == BLOCKING
    assert non_blocking_names == NON_BLOCKING

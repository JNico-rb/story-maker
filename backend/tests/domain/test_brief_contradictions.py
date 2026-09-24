"""Contradicciones C1-C5, por tabla (008-C10)."""

from __future__ import annotations

import datetime as dt

import pytest

from story_maker.domain.brief import (
    BriefContent,
    CloseOne,
    Recipient,
    Recollection,
    Trait,
    contradictions,
)

CREATED_AT = dt.date(2026, 9, 24)


def _content(**overrides: object) -> BriefContent:
    base = BriefContent(
        recipient=Recipient(name="Marta", age=40, traits=[Trait(statement="curiosa")]),
        recollections=[Recollection(statement="algo", age=8, place="un lugar")],
        occasion="birthday",
        genre="adventure",
        tone="tender",
        length="medium",
        dedication="Para Marta",
        banned_asked=True,
    )
    return base.model_copy(update=overrides)


def _rules(content: BriefContent, created_at: dt.date = CREATED_AT) -> list[str]:
    return [c.rule for c in contradictions(content, created_at)]


@pytest.mark.parametrize(
    ("age", "genre", "expects_c1"),
    [
        (11, "romance", True),
        (11, "drama", True),
        (12, "romance", False),
        (11, "fable", False),
    ],
)
def test_c1_age_versus_genre(age: int, genre: str, expects_c1: bool) -> None:
    content = _content(recipient=Recipient(name="M", age=age, traits=[Trait(statement="x")]))
    content = content.model_copy(update={"genre": genre})

    assert ("C1" in _rules(content)) == expects_c1


@pytest.mark.parametrize(
    ("age", "tone", "expects_c2"),
    [
        (11, "unsettling", True),
        (12, "unsettling", False),
        (11, "tender", False),
    ],
)
def test_c2_age_versus_tone(age: int, tone: str, expects_c2: bool) -> None:
    content = _content(recipient=Recipient(name="M", age=age, traits=[Trait(statement="x")]))
    content = content.model_copy(update={"tone": tone})

    assert ("C2" in _rules(content)) == expects_c2


@pytest.mark.parametrize(
    ("age", "occasion", "expects_c3"),
    [
        (17, "wedding", True),
        (17, "anniversary", True),
        (49, "retirement", True),
        (18, "wedding", False),
        (50, "retirement", False),
        (10, "birthday", False),
    ],
)
def test_c3_occasion_versus_age(age: int, occasion: str, expects_c3: bool) -> None:
    content = _content(recipient=Recipient(name="M", age=age, traits=[Trait(statement="x")]))
    content = content.model_copy(update={"occasion": occasion})

    assert ("C3" in _rules(content)) == expects_c3


@pytest.mark.parametrize(
    ("birth_date", "age", "created_at", "expects_c4"),
    [
        (dt.date(1986, 9, 24), 40, CREATED_AT, False),
        (dt.date(1986, 9, 25), 40, CREATED_AT, True),
        (dt.date(2000, 2, 29), 26, dt.date(2026, 2, 28), True),
        (dt.date(2000, 2, 29), 26, dt.date(2026, 3, 1), False),
        (dt.date(1986, 9, 24), 40, dt.date(2027, 1, 10), False),
    ],
)
def test_c4_declared_birth_date_versus_age(
    birth_date: dt.date, age: int, created_at: dt.date, expects_c4: bool
) -> None:
    content = _content(
        recipient=Recipient(name="M", age=age, birth_date=birth_date, traits=[Trait(statement="x")])
    )

    assert ("C4" in _rules(content, created_at)) == expects_c4


def test_c4_also_applies_to_a_close_one() -> None:
    content = _content(
        close_ones=[
            CloseOne(
                name="Toby",
                relation="mascota",
                species="animal",
                age=5,
                birth_date=dt.date(2019, 1, 1),
            )
        ]
    )

    found = contradictions(content, CREATED_AT)
    assert any(c.rule == "C4" and "close_ones[0]" in c.fields[0] for c in found)


@pytest.mark.parametrize(
    ("recollection", "expects_c5"),
    [
        (Recollection(statement="x", age=41, place="p"), True),
        (Recollection(statement="x", age=40, place="p"), False),
        (Recollection(statement="x", year=1986, place="p"), False),
        (Recollection(statement="x", year=2026, place="p"), False),
        (Recollection(statement="x", year=1985, place="p"), True),
        (Recollection(statement="x", year=2027, place="p"), True),
    ],
)
def test_c5_recollection_versus_age_or_year(recollection: Recollection, expects_c5: bool) -> None:
    content = _content(recollections=[recollection])

    assert ("C5" in _rules(content)) == expects_c5


def test_c5_with_a_declared_birth_date_and_a_recollection_before_it() -> None:
    content = _content(
        recipient=Recipient(
            name="M", age=40, birth_date=dt.date(1986, 9, 24), traits=[Trait(statement="x")]
        ),
        recollections=[Recollection(statement="x", year=1985, place="p")],
    )

    assert "C5" in _rules(content)


def test_without_the_age_none_of_c1_to_c5_evaluate() -> None:
    content = _content(
        recipient=Recipient(name="M", age=None, traits=[Trait(statement="x")]),
        occasion="wedding",
        recollections=[Recollection(statement="x", age=41, place="p")],
    )

    assert _rules(content) == []


def test_a_brief_with_two_contradictions_lists_both() -> None:
    content = _content(
        recipient=Recipient(name="M", age=11, traits=[Trait(statement="x")]),
        genre="romance",
        tone="unsettling",
    )

    assert sorted(_rules(content)) == ["C1", "C2"]

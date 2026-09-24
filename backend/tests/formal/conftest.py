"""Cronología de fixture de la spec 007 (§ Comportamiento observable, «Datos de los casos»)."""

from __future__ import annotations

import datetime as dt

import pytest

from story_maker.formal.chronology import (
    Chronology,
    ChronologyCharacter,
    ChronologyEvent,
    Presence,
)

RECIPIENT, GRANDMOTHER, DOG = 11, 12, 13
PLACE_A, PLACE_B = 21, 22


def fixture_chronology() -> Chronology:
    """El destinatario (11), la abuela (12), el perro (13); lugares 21 y 22; eventos 31, 32 (brief),
    41, 42 (registrados) y 51 (planificado)."""
    return Chronology(
        events=(
            ChronologyEvent(
                id=31,
                moment=dt.datetime(1998, 5, 14, 12, 0),
                place_id=PLACE_A,
                presences=(Presence(RECIPIENT, 8), Presence(GRANDMOTHER)),
                type="ordinary",
                excluded_character_id=None,
                analepsis=False,
                origin="brief",
                chapter=None,
                beat=None,
            ),
            ChronologyEvent(
                id=32,
                moment=dt.datetime(2010, 9, 1, 12, 0),
                place_id=PLACE_B,
                presences=(Presence(RECIPIENT),),
                type="exclusion",
                excluded_character_id=GRANDMOTHER,
                analepsis=False,
                origin="brief",
                chapter=None,
                beat=None,
            ),
            ChronologyEvent(
                id=41,
                moment=dt.datetime(2026, 3, 2, 10, 0),
                place_id=PLACE_A,
                presences=(Presence(RECIPIENT), Presence(DOG)),
                type="ordinary",
                excluded_character_id=None,
                analepsis=False,
                origin="recorded",
                chapter=1,
                beat=1,
            ),
            ChronologyEvent(
                id=42,
                moment=dt.datetime(2005, 7, 1, 18, 0),
                place_id=PLACE_B,
                presences=(Presence(RECIPIENT), Presence(GRANDMOTHER)),
                type="ordinary",
                excluded_character_id=None,
                analepsis=True,
                origin="recorded",
                chapter=2,
                beat=1,
            ),
            ChronologyEvent(
                id=51,
                moment=dt.datetime(2026, 5, 10, 9, 0),
                place_id=PLACE_A,
                presences=(Presence(RECIPIENT),),
                type="ordinary",
                excluded_character_id=None,
                analepsis=False,
                origin="planned",
                chapter=3,
                beat=2,
            ),
        ),
        characters=(
            ChronologyCharacter(RECIPIENT, dt.date(1990, 5, 14)),
            ChronologyCharacter(GRANDMOTHER, dt.date(1936, 2, 29)),
            ChronologyCharacter(DOG, None),
        ),
        novum_date=dt.date(2024, 11, 1),
    )


@pytest.fixture
def chronology() -> Chronology:
    return fixture_chronology()

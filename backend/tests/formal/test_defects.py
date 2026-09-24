"""Traducción del testigo a `Defecto` de `cronologia-lean` (007-C07, 007-C08)."""

from __future__ import annotations

import datetime as dt

from story_maker.formal.defects import Defect, defects_from
from story_maker.formal.result import ChronologyResult
from story_maker.store.story_bible import (
    BirthEntry,
    CharacterEntry,
    Chronology,
    EventEntry,
    PlaceEntry,
    PresenceEntry,
    StoryBible,
)

ALL_HOLD = dict.fromkeys(("T1", "T2", "T3", "T4", "T5"), True)


def entry(
    id_: int,
    moment: dt.datetime,
    place: int,
    *present: int,
    origin: str = "recorded",
    chapter: int | None = None,
    beat: int | None = None,
    excluded: int | None = None,
) -> EventEntry:
    return EventEntry(
        id=id_,
        statement=f"enunciado {id_}",
        moment=moment,
        place_id=place,
        presences=tuple(PresenceEntry(p, None) for p in present),
        type="exclusion" if excluded is not None else "ordinary",
        excluded_character_id=excluded,
        analepsis=False,
        origin=origin,
        chapter=chapter,
        beat=beat,
    )


def bible(*events: EventEntry) -> StoryBible:
    characters = (
        CharacterEntry(11, "recipient", "person", "Marta", dt.date(1990, 5, 14), "brief"),
        CharacterEntry(12, "close_one", "person", "Rosa", dt.date(1936, 2, 29), "brief"),
    )
    places = (
        PlaceEntry(21, "la feria del pueblo", "", "brief"),
        PlaceEntry(22, "la estación", "", "brief"),
        PlaceEntry(23, "el faro", "", "invented"),
    )
    return StoryBible(
        version_id=1,
        present_year=2026,
        world=None,
        characters=characters,
        places=places,
        facts=(),
        chronology=Chronology(
            events=events,
            births=(BirthEntry(11, dt.date(1990, 5, 14)), BirthEntry(12, dt.date(1936, 2, 29))),
            novum_date=dt.date(2024, 11, 1),
        ),
    )


# --- 007-C07 ---------------------------------------------------------------------------------


def test_a_witness_with_narrated_events_gives_one_defect_per_chapter() -> None:
    story = bible(
        entry(32, dt.datetime(2010, 9, 1, 12, 0), 22, origin="brief", excluded=12),
        entry(43, dt.datetime(2026, 5, 2, 18, 30), 21, 11, chapter=3, beat=1),
        entry(44, dt.datetime(2026, 5, 1, 9, 0), 23, 11, chapter=5, beat=4),
        entry(71, dt.datetime(2026, 8, 15, 12, 0), 23, 12, chapter=7, beat=2),
    )
    result = ChronologyResult(
        "failed",
        holds={**ALL_HOLD, "T1": False, "T4": False},
        witnesses={"T4": (12, 32, 71), "T1": (43, 44)},
    )

    defects = defects_from(result, story)

    assert len(defects) == 3
    assert all(
        d.validator == "cronologia-lean" and d.criterion is None and d.blocking for d in defects
    )
    t4 = [d for d in defects if d.message.startswith("T4")]
    t1 = [d for d in defects if d.message.startswith("T1")]
    assert [d.chapter for d in t4] == [7]
    assert sorted(d.chapter or 0 for d in t1) == [3, 5]
    assert t1[0].message == t1[1].message
    for fragment in (
        "Rosa",
        "la estación",
        "el faro",
        "del brief",
        "registrado",
        "capítulo 7, beat 2",
        "1 de septiembre de 2010 a las 12:00",
        "15 de agosto de 2026 a las 12:00",
    ):
        assert fragment in t4[0].message
    for fragment in (
        "la feria del pueblo",
        "el faro",
        "capítulo 3, beat 1",
        "capítulo 5, beat 4",
        "2 de mayo de 2026 a las 18:30",
        "1 de mayo de 2026 a las 09:00",
    ):
        assert fragment in t1[0].message
    assert "enunciado" not in t4[0].message + t1[0].message


# --- 007-C08 ---------------------------------------------------------------------------------


def test_a_witness_with_only_brief_events_gives_one_defect_without_chapter() -> None:
    story = bible(
        entry(31, dt.datetime(1998, 5, 14, 12, 0), 21, 11, 12, origin="brief"),
        entry(33, dt.datetime(1998, 5, 14, 12, 0), 22, 11, origin="brief"),
    )
    result = ChronologyResult(
        "failed",
        holds={**ALL_HOLD, "T3": False},
        witnesses={"T3": (11, 31, 33)},
    )

    defects = defects_from(result, story)

    assert defects == (Defect("cronologia-lean", None, True, None, defects[0].message),)
    message = defects[0].message
    assert message.startswith("T3")
    for fragment in (
        "Marta",
        "la feria del pueblo",
        "la estación",
        "del brief",
        "14 de mayo de 1998",
    ):
        assert fragment in message
    assert "capítulo" not in message


def test_a_result_that_is_not_failed_gives_no_defects() -> None:
    story = bible()

    assert defects_from(ChronologyResult("passed", holds=ALL_HOLD), story) == ()
    assert defects_from(ChronologyResult("error", reason="no compila"), story) == ()

"""Generador del `FicheroDeCronologia` (007-C01 a 007-C05, 007-I3, 007-I4)."""

from __future__ import annotations

import calendar
import datetime as dt
import re
from dataclasses import dataclass, replace

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from story_maker.formal.chronology import (
    Chronology,
    ChronologyCharacter,
    ChronologyEvent,
    Presence,
)
from story_maker.formal.generator import generate_chronology_file

# --- Lectura del fichero generado, solo para las pruebas -------------------------------------

_EVENT_RE = re.compile(
    r"\{ id := (?P<id>\d+), momento := ⟨(?P<moment>\d+, \d+, \d+, \d+, \d+)⟩, "
    r"capitulo := (?P<chapter>none|some \d+), beat := (?P<beat>none|some \d+), "
    r"lugar := (?P<place>\d+), presentes := \[(?P<presences>[^\]]*)\], "
    r"tipo := (?P<type>\.ordinario|\.excluyente \d+), analepsis := (?P<analepsis>true|false) \}"
)
_PRESENCE_RE = re.compile(r"⟨(\d+), (none|some \d+)⟩")
_BIRTH_RE = re.compile(r"⟨(\d+), ⟨(\d+), (\d+), (\d+)⟩⟩")
_NOVUM_RE = re.compile(r"novum := ⟨(\d+), (\d+), (\d+)⟩")


def _optional(text: str) -> int | None:
    return None if text == "none" else int(text.removeprefix("some "))


@dataclass(frozen=True)
class ParsedEvent:
    id: int
    moment: tuple[int, int, int, int, int]
    chapter: int | None
    beat: int | None
    place: int
    presences: tuple[tuple[int, int | None], ...]
    excluded: int | None
    analepsis: bool


@dataclass(frozen=True)
class ParsedFile:
    events: tuple[ParsedEvent, ...]
    births: dict[int, tuple[int, int, int]]
    novum: tuple[int, int, int] | None


def parse(source: str) -> ParsedFile:
    events = []
    for match in _EVENT_RE.finditer(source):
        year, month, day, hour, minute = (int(part) for part in match["moment"].split(", "))
        events.append(
            ParsedEvent(
                id=int(match["id"]),
                moment=(year, month, day, hour, minute),
                chapter=_optional(match["chapter"]),
                beat=_optional(match["beat"]),
                place=int(match["place"]),
                presences=tuple(
                    (int(p), _optional(age)) for p, age in _PRESENCE_RE.findall(match["presences"])
                ),
                excluded=(
                    None
                    if match["type"] == ".ordinario"
                    else int(match["type"].removeprefix(".excluyente "))
                ),
                analepsis=match["analepsis"] == "true",
            )
        )
    births_block = source.partition("nacimientos := [")[2].partition("]")[0]
    births = {int(c): (int(y), int(m), int(d)) for c, y, m, d in _BIRTH_RE.findall(births_block)}
    novum = _NOVUM_RE.search(source)
    return ParsedFile(
        events=tuple(events),
        births=births,
        novum=(int(novum[1]), int(novum[2]), int(novum[3])) if novum else None,
    )


# Vocabulario completo del fichero: la plantilla de la biblioteca, sin texto de la story bible.
TEMPLATE_WORDS = {
    "import",
    "Chronology",
    "open",
    "def",
    "cronologia",
    "Cronologia",
    "where",
    "novum",
    "nacimientos",
    "eventos",
    "id",
    "momento",
    "capitulo",
    "beat",
    "lugar",
    "presentes",
    "tipo",
    "ordinario",
    "excluyente",
    "analepsis",
    "true",
    "false",
    "some",
    "none",
    "eval",
    "IO",
    "println",
    "CRONOLOGIA",
    "LEAN",
    "informe",
    "theorem",
    "mp",
    "by",
    "decide",
    "kernel",
    "print",
    "axioms",
    *(f"T{n}" for n in range(1, 6)),
    *(f"cumpleT{n}" for n in range(1, 6)),
    *(f"compruebaT{n}_decide" for n in range(1, 6)),
}


def words(source: str) -> set[str]:
    return set(re.findall(r"[^\W\d]\w*", source))


# --- 007-C01 ---------------------------------------------------------------------------------


def test_the_file_carries_the_recorded_chronology_of_the_version_and_nothing_else(
    chronology: Chronology,
) -> None:
    parsed = parse(generate_chronology_file(chronology, k=1))
    by_id = {event.id: event for event in parsed.events}
    shift = 400

    assert sorted(by_id) == [31, 32, 41, 42]
    assert by_id[31] == ParsedEvent(
        id=31,
        moment=(1998 + shift, 5, 14, 12, 0),
        chapter=None,
        beat=None,
        place=21,
        presences=((11, 8), (12, None)),
        excluded=None,
        analepsis=False,
    )
    assert by_id[32] == ParsedEvent(
        id=32,
        moment=(2010 + shift, 9, 1, 12, 0),
        chapter=None,
        beat=None,
        place=22,
        presences=((11, None),),
        excluded=12,
        analepsis=False,
    )
    assert by_id[41] == ParsedEvent(
        id=41,
        moment=(2026 + shift, 3, 2, 10, 0),
        chapter=1,
        beat=1,
        place=21,
        presences=((11, None), (13, None)),
        excluded=None,
        analepsis=False,
    )
    assert by_id[42] == ParsedEvent(
        id=42,
        moment=(2005 + shift, 7, 1, 18, 0),
        chapter=2,
        beat=1,
        place=22,
        presences=((11, None), (12, None)),
        excluded=None,
        analepsis=True,
    )
    assert parsed.births == {11: (1990 + shift, 5, 14), 12: (1936 + shift, 2, 29)}
    assert parsed.novum == (2024 + shift, 11, 1)


def test_the_file_has_only_ids_dates_numbers_and_yes_no_values(chronology: Chronology) -> None:
    source = generate_chronology_file(chronology, k=1)

    assert source
    assert words(source) <= TEMPLATE_WORDS


def test_the_planned_event_is_left_out(chronology: Chronology) -> None:
    source = generate_chronology_file(chronology, k=1)

    assert "id := 51" not in source
    assert "id := 31" in source


# --- 007-C02 ---------------------------------------------------------------------------------

REAL_YEARS = {1936, 1990, 1998, 2005, 2010, 2024, 2026}


def numbers(source: str) -> set[int]:
    return {int(n) for n in re.findall(r"\d+", source)}


def mask_years(source: str, years: set[int]) -> str:
    return re.sub(r"\d+", lambda m: "AÑO" if int(m[0]) in years else m[0], source)


@pytest.mark.parametrize("k", [1, 3, 10])
def test_ids_are_the_row_ids_and_dates_shift_by_400_k_years(chronology: Chronology, k: int) -> None:
    parsed = parse(generate_chronology_file(chronology, k=k))
    recorded = [e for e in chronology.events if e.origin != "planned"]

    assert [e.id for e in parsed.events] == [e.id for e in recorded]
    for real, written in zip(recorded, parsed.events, strict=True):
        m = real.moment
        assert written.moment == (m.year + 400 * k, m.month, m.day, m.hour, m.minute)
        assert written.place == real.place_id
        assert [p for p, _ in written.presences] == [p.character_id for p in real.presences]
        assert written.excluded == real.excluded_character_id
    assert parsed.births == {
        c.id: (c.birth_date.year + 400 * k, c.birth_date.month, c.birth_date.day)
        for c in chronology.characters
        if c.birth_date is not None
    }
    n = chronology.novum_date
    assert parsed.novum == (n.year + 400 * k, n.month, n.day)


@pytest.mark.parametrize("k", range(1, 11))
def test_the_file_contains_none_of_the_real_years(chronology: Chronology, k: int) -> None:
    assert numbers(generate_chronology_file(chronology, k=k)).isdisjoint(REAL_YEARS)


def test_the_file_does_not_record_k(chronology: Chronology) -> None:
    """Con k distinto, los ficheros solo difieren en los años: k no queda escrito en él."""
    shifted = {year + 400 * k for year in REAL_YEARS for k in (2, 7)}

    assert mask_years(generate_chronology_file(chronology, k=2), shifted) == mask_years(
        generate_chronology_file(chronology, k=7), shifted
    )


# --- 007-C03 ---------------------------------------------------------------------------------


def inferred_k(source: str, chronology: Chronology) -> int:
    parsed = parse(source)
    assert parsed.novum is not None
    shift = parsed.novum[0] - chronology.novum_date.year
    assert shift % 400 == 0
    return shift // 400


def test_k_is_drawn_at_random_for_each_file_between_1_and_10(chronology: Chronology) -> None:
    sources = [generate_chronology_file(chronology) for _ in range(300)]
    ks = [inferred_k(source, chronology) for source in sources]

    assert set(ks) == set(range(1, 11))
    by_k = dict(zip(ks, sources, strict=True))
    shifted = {year + 400 * k for year in REAL_YEARS for k in by_k}
    masked = {mask_years(source, shifted) for source in by_k.values()}
    assert len(masked) == 1


# --- 007-C04 ---------------------------------------------------------------------------------


def reordered(chronology: Chronology) -> Chronology:
    """La misma cronología, leída en otro orden de inserción: todo al revés."""
    return replace(
        chronology,
        events=tuple(
            replace(e, presences=tuple(reversed(e.presences))) for e in reversed(chronology.events)
        ),
        characters=tuple(reversed(chronology.characters)),
    )


def test_the_same_chronology_and_k_give_the_same_file_byte_for_byte(
    chronology: Chronology,
) -> None:
    first = generate_chronology_file(chronology, k=4)
    second = generate_chronology_file(reordered(chronology), k=4)

    assert first.encode("utf-8") == second.encode("utf-8")
    assert [e.id for e in parse(second).events] == [31, 32, 41, 42]


# --- 007-C05 ---------------------------------------------------------------------------------


def completed_years(birth: tuple[int, int, int], moment: tuple[int, ...]) -> int:
    """Edad en años cumplidos (`domain-knowledge.md` §5.2): se nace a las 00:00 y un 29 de
    febrero cumple el 1 de marzo en los años no bisiestos."""
    year, month, day = moment[:3]
    b_year, b_month, b_day = birth
    birthday = (b_month, b_day)
    if birthday == (2, 29) and not calendar.isleap(year):
        birthday = (3, 1)
    return year - b_year - (1 if (month, day) < birthday else 0)


def leap_day_chronology(chronology: Chronology) -> Chronology:
    def event(id_: int, moment: dt.datetime, age: int) -> ChronologyEvent:
        return ChronologyEvent(
            id=id_,
            moment=moment,
            place_id=21,
            presences=(Presence(12, age),),
            type="ordinary",
            excluded_character_id=None,
            analepsis=False,
            origin="recorded",
            chapter=id_ - 60,
            beat=1,
        )

    return replace(
        chronology,
        events=(
            event(61, dt.datetime(2026, 2, 28, 12, 0), 89),
            event(62, dt.datetime(2026, 3, 1, 0, 0), 90),
            event(63, dt.datetime(2028, 2, 29, 0, 0), 92),
        ),
    )


@pytest.mark.parametrize("k", range(1, 11))
def test_the_29th_of_february_and_the_ages_survive_the_shift(
    chronology: Chronology, k: int
) -> None:
    parsed = parse(generate_chronology_file(leap_day_chronology(chronology), k=k))
    birth = parsed.births[12]
    moments = {e.id: e.moment for e in parsed.events}

    assert birth[1:] == (2, 29)
    assert calendar.isleap(birth[0])
    dt.date(*birth)  # la fecha existe
    assert not calendar.isleap(moments[61][0])
    assert calendar.isleap(moments[63][0])
    assert [completed_years(birth, moments[i]) for i in (61, 62, 63)] == [89, 90, 92]
    assert [
        completed_years((1936, 2, 29), m) for m in ((2026, 2, 28), (2026, 3, 1), (2028, 2, 29))
    ] == [89, 90, 92]


# --- Cronologías generadas (007-I3, 007-I4) --------------------------------------------------

LEAP_BIRTHS = st.sampled_from([dt.date(1936, 2, 29), dt.date(2000, 2, 29), dt.date(1904, 2, 29)])
BIRTHS = st.none() | LEAP_BIRTHS | st.dates(dt.date(1900, 1, 1), dt.date(2026, 12, 31))
MOMENTS = st.datetimes(dt.datetime(1900, 1, 1), dt.datetime(2030, 12, 31, 23, 59)).map(
    lambda m: m.replace(second=0, microsecond=0)
)


@st.composite
def chronologies(draw: st.DrawFn) -> Chronology:
    character_ids = draw(st.lists(st.integers(1, 500), unique=True, min_size=1, max_size=6))
    characters = tuple(ChronologyCharacter(c, draw(BIRTHS)) for c in character_ids)
    events = []
    for event_id in draw(st.lists(st.integers(1, 5000), unique=True, max_size=10)):
        present = draw(st.lists(st.sampled_from(character_ids), unique=True, max_size=3))
        exclusion = draw(st.booleans())
        chapter = draw(st.none() | st.integers(1, 10))
        events.append(
            ChronologyEvent(
                id=event_id,
                moment=draw(MOMENTS),
                place_id=draw(st.integers(1, 300)),
                presences=tuple(
                    Presence(c, draw(st.none() | st.integers(0, 120))) for c in present
                ),
                type="exclusion" if exclusion else "ordinary",
                excluded_character_id=draw(st.sampled_from(character_ids)) if exclusion else None,
                analepsis=draw(st.booleans()),
                origin=draw(st.sampled_from(["brief", "planned", "recorded"])),
                chapter=chapter,
                beat=draw(st.integers(1, 6)) if chapter is not None else None,
            )
        )
    novum = draw(st.dates(dt.date(1950, 1, 1), dt.date(2025, 12, 31)))
    return Chronology(events=tuple(events), characters=characters, novum_date=novum)


@settings(max_examples=200)
@given(chronology=chronologies(), k=st.none() | st.integers(1, 10))
def test_the_file_never_carries_personal_data_only_ids_dates_numbers_and_yes_no(
    chronology: Chronology, k: int | None
) -> None:
    source = generate_chronology_file(chronology, k=k)

    assert words(source) <= TEMPLATE_WORDS

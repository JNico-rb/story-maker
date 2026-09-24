"""Generador del `FicheroDeCronologia` (007-C01 a 007-C05, 007-I3, 007-I4)."""

from __future__ import annotations

import re
from dataclasses import dataclass

import pytest

from story_maker.formal.chronology import Chronology
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

"""Los dos avisos ligeros de cronología del lint en vivo: un personaje que reaparece tras su evento
excluyente y una edad escrita que no cuadra con su fecha de nacimiento. No sustituyen a Lean
(`architecture.md` §10.3, §18 «Lean frente a Python»; 019-C07, 019-C08)."""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from story_maker.pipeline.manual_edit.diagnostics import Diagnostic
from story_maker.store.models import Character, Event, Novel, Version


@dataclass(frozen=True)
class Exclusion:
    character: str
    moment: dt.datetime
    origin: str
    chapter: int | None


@dataclass(frozen=True)
class Timeline:
    """Los momentos del capítulo (los de sus eventos registrados; sin ellos, el año presente) y los
    eventos excluyentes que cuentan: de origen brief o registrados."""

    moments: tuple[dt.datetime, ...]
    present_year: int
    exclusions: tuple[Exclusion, ...]

    @property
    def last_moment(self) -> dt.datetime:
        return max(self.moments) if self.moments else dt.datetime(self.present_year, 1, 1)


def load_timeline(session: Session, version_id: int, chapter: int) -> Timeline:
    version = session.get_one(Version, version_id)
    novel = session.get_one(Novel, version.novel_id)
    recorded = session.query(Event.moment).filter(
        Event.version_id == version_id, Event.origin == "recorded", Event.chapter == chapter
    )
    excluding = (
        session.query(Event, Character.canonical_name)
        .join(Character, Character.id == Event.excluded_character_id)
        .filter(
            Event.version_id == version_id,
            Event.type == "exclusion",
            Event.origin.in_(("brief", "recorded")),
        )
        .order_by(Event.moment, Event.id)
    )
    return Timeline(
        moments=tuple(row[0] for row in recorded),
        present_year=novel.created_at.year,
        exclusions=tuple(
            Exclusion(name, event.moment, event.origin, event.chapter) for event, name in excluding
        ),
    )


def _first_mention(text: str, name: str) -> re.Match[str] | None:
    return re.search(rf"(?<!\w){re.escape(name)}(?!\w)", text)


def reappearances(text: str, timeline: Timeline) -> list[Diagnostic]:
    """El nombre canónico de un excluido cuyo evento excluyente es anterior al último momento del
    capítulo, en su primera mención."""
    found = []
    for exclusion in timeline.exclusions:
        if exclusion.moment >= timeline.last_moment:
            continue
        mention = _first_mention(text, exclusion.character)
        if mention is None:
            continue
        where = (
            "de origen brief"
            if exclusion.origin == "brief"
            else f"registrado en el capítulo {exclusion.chapter}"
        )
        found.append(
            Diagnostic(
                "cronologia",
                f"{exclusion.character} reaparece tras su evento excluyente ({where}, "
                f"{exclusion.moment:%d-%m-%Y})",
                blocking=False,
                start=mention.start(),
                end=mention.end(),
                extra={
                    "character": exclusion.character,
                    "event": {
                        "origin": exclusion.origin,
                        "chapter": exclusion.chapter,
                        "moment": exclusion.moment.isoformat(),
                    },
                },
            )
        )
    return found


_UNITS = ("uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve")
_TEENS = ("diez", "once", "doce", "trece", "catorce", "quince")
_SIXTEEN_TO_29 = [
    "dieciseis",
    "diecisiete",
    "dieciocho",
    "diecinueve",
    "veinte",
    "veintiuno",
    "veintidos",
    "veintitres",
    "veinticuatro",
    "veinticinco",
    "veintiseis",
    "veintisiete",
    "veintiocho",
    "veintinueve",
]
_TENS = ("treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa")


def _number_words() -> dict[str, int]:
    words = {word: value for value, word in enumerate(_UNITS, start=1)}
    words.update({"un": 1, "una": 1, "veintiun": 21, "veintiuna": 21})
    words.update({word: value for value, word in enumerate(_TEENS, start=10)})
    words.update({word: value for value, word in enumerate(_SIXTEEN_TO_29, start=16)})
    for tens, word in enumerate(_TENS, start=3):
        words[word] = tens * 10
        for unit, unit_word in enumerate(_UNITS, start=1):
            words[f"{word} y {unit_word}"] = tens * 10 + unit
        words[f"{word} y un"] = words[f"{word} y una"] = tens * 10 + 1
    return words


NUMBER_WORDS = _number_words()
_AGE = re.compile(r"(?<!\w)(\w+)\s+(\d{1,2}|[^\W\d_]+(?:\s+y\s+[^\W\d_]+)?)\s+años(?!\w)")
_BEFORE_AGE = re.compile(r"(ten|tien|tuv|tendr|cumpl)\w*|de", re.IGNORECASE)
_SENTENCE = re.compile(r"[^.!?…]+[.!?…]*")


def _fold(word: str) -> str:
    return (
        word.lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )


def written_age(number: str) -> int | None:
    """Un número en cifras, o en palabras hasta «noventa y nueve»."""
    if number.isdigit():
        return int(number)
    return NUMBER_WORDS.get(" ".join(_fold(number).split()))


def age_at(birth: dt.date, moment: dt.date) -> int:
    return moment.year - birth.year - ((moment.month, moment.day) < (birth.month, birth.day))


def possible_ages(birth: dt.date, timeline: Timeline) -> list[int]:
    """Sus edades en los momentos del capítulo; sin ellos, a lo largo del año presente."""
    if timeline.moments:
        moments = [m.date() for m in timeline.moments]
    else:
        moments = [dt.date(timeline.present_year, 1, 1), dt.date(timeline.present_year, 12, 31)]
    return sorted({age_at(birth, m) for m in moments})


def _last_name_before(sentence: str, end: int, births: dict[str, dt.date | None]) -> str | None:
    last: tuple[int, str] | None = None
    for name in births:
        for mention in re.finditer(rf"(?<!\w){re.escape(name)}(?!\w)", sentence[:end]):
            if last is None or mention.start() > last[0]:
                last = (mention.start(), name)
    return last[1] if last is not None else None


def wrong_ages(
    text: str, timeline: Timeline, births: dict[str, dt.date | None]
) -> list[Diagnostic]:
    """Una edad escrita («tenía 36 años», «de treinta y cinco años») que no es ninguna de las del
    último nombre canónico anterior de su frase en los momentos del capítulo."""
    found = []
    for sentence in _SENTENCE.finditer(text):
        body = sentence.group(0)
        for match in _AGE.finditer(body):
            age = written_age(match.group(2))
            if age is None or not _BEFORE_AGE.fullmatch(match.group(1)):
                continue
            name = _last_name_before(body, match.start(), births)
            birth = births.get(name) if name is not None else None
            if birth is None:
                continue
            expected = possible_ages(birth, timeline)
            if age in expected:
                continue
            start = sentence.start() + match.start(2)
            found.append(
                Diagnostic(
                    "cronologia",
                    f"{name} tiene {age} años en el texto; por su fecha de nacimiento, "
                    f"{' o '.join(str(e) for e in expected)}",
                    blocking=False,
                    start=start,
                    end=start + len(match.group(2)),
                    extra={"character": name, "written_age": age, "expected": expected},
                )
            )
    return found


def load_births(session: Session, version_id: int) -> dict[str, dt.date | None]:
    rows = session.query(Character).filter(Character.version_id == version_id)
    return {c.canonical_name: c.birth_date for c in rows.order_by(Character.id)}

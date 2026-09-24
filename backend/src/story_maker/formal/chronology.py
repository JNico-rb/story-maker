"""La `Cronologia` de una versión, tal como la lee el generador (`definitions.md` §2).

Solo lleva lo que el fichero Lean puede contener: ids de fila, fechas, números y valores sí/no.
Los nombres y los enunciados de la story bible no entran aquí (007-I3).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Literal

EventType = Literal["ordinary", "exclusion"]
EventOrigin = Literal["brief", "planned", "recorded"]


@dataclass(frozen=True)
class Presence:
    """Un personaje presente en un evento, con su edad declarada si la fuente la fija."""

    character_id: int
    declared_age: int | None = None


@dataclass(frozen=True)
class ChronologyEvent:
    id: int
    moment: dt.datetime
    place_id: int
    presences: tuple[Presence, ...]
    type: EventType
    excluded_character_id: int | None
    analepsis: bool
    origin: EventOrigin
    chapter: int | None
    beat: int | None


@dataclass(frozen=True)
class ChronologyCharacter:
    id: int
    birth_date: dt.date | None


@dataclass(frozen=True)
class Chronology:
    events: tuple[ChronologyEvent, ...]
    characters: tuple[ChronologyCharacter, ...]
    novum_date: dt.date

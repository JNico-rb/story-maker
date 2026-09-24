"""Vista de la story bible inicial que necesita `outline` (010-C10..C16) y, más adelante, el
ensamblaje de la ventana del planner (010-C06).

Es una vista mínima y de solo lectura, no la story bible completa de `definitions.md` §2: solo
los campos que estos pasos necesitan (nombres para las referencias, ids de hechos y elementos
personales para la asignación de obligatorios, año presente). Cuando la 009
(`store/story_bible.py`, `store/brief_canon.py`) esté en V2, quien arranque la fase construirá
esta vista desde sus repositorios; hasta entonces la construyen las pruebas directamente. No
copia ni importa código de la 009 (instrucción del carril, 2026-09-24)."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

WORLD_NAME = "world"


@dataclass(frozen=True)
class PersonalElement:
    """Un `ElementoPersonal` del brief, tal como lo necesita `outline` para 010-C12."""

    id: str
    label: str
    mandatory: bool


@dataclass(frozen=True)
class FactRef:
    """Un `Hecho` de la story bible inicial. `outline` (010-C10..C16) solo mira `id`; la
    ventana del planner (010-C06) también lleva `mandatory` y `personal_element_id`."""

    id: str
    mandatory: bool = False
    personal_element_id: str | None = None


@dataclass(frozen=True)
class EventRef:
    """Un `Evento` de origen brief, para la ventana del planner (010-C06)."""

    statement: str
    moment: dt.datetime
    place: str
    present: tuple[str, ...] = ()
    excluded: str | None = None


@dataclass(frozen=True)
class StoryBibleView:
    present_year: int
    character_names: tuple[str, ...] = ()
    place_names: tuple[str, ...] = ()
    fact_ids: tuple[str, ...] = ()
    personal_elements: tuple[PersonalElement, ...] = ()
    facts: tuple[FactRef, ...] = ()
    events: tuple[EventRef, ...] = ()

    @property
    def mandatory_elements(self) -> tuple[PersonalElement, ...]:
        return tuple(e for e in self.personal_elements if e.mandatory)

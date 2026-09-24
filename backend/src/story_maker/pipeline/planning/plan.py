"""Entrega `submit_plan`: su schema y sus campos narrativos (010-C08, 010-C09).

`definitions.md` §2 (Mundo, Personaje, Lugar, Hecho), §3 (Outline, Beat, StyleSheet), §11.2."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field

from story_maker.domain.constants import MAX_CONSEQUENCES, MIN_CONSEQUENCES

NovumScope = Literal["technological", "social", "cognitive"]
Species = Literal["person", "animal", "artificial"]
EventType = Literal["ordinary", "exclusion"]
Narrator = Literal["first", "third"]
Tense = Literal["past", "present"]
Treatment = Literal["tu", "usted"]

# La palabra clave con la que un hecho inventado declara al mundo como sujeto (`Hecho.subject_type
# == "world"` en `store/models.py`; aquí no hay tabla, solo esta referencia por nombre).
WORLD_SUBJECT = "world"


class WorldSubmission(BaseModel):
    novum_description: str
    novum_scope: NovumScope
    novum_date: dt.date
    consequences: list[str] = Field(min_length=MIN_CONSEQUENCES, max_length=MAX_CONSEQUENCES)


class InventedCharacter(BaseModel):
    name: str
    species: Species


class InventedPlace(BaseModel):
    name: str
    description: str = ""


class InventedFact(BaseModel):
    """`id` es del plan, no de la story bible: así un beat puede referenciarlo (010-C14)."""

    id: str
    subject: str
    attribute: str
    value: str


class PlannedEvent(BaseModel):
    statement: str
    moment: dt.datetime
    place: str
    type: EventType
    excluded: str | None = None
    analepsis: bool
    present: tuple[str, ...] = ()


class Revelation(BaseModel):
    theme: str
    content: str


class Beat(BaseModel):
    number: int
    description: str
    events: tuple[PlannedEvent, ...] = ()
    characters: tuple[str, ...] = ()
    facts_used: tuple[str, ...] = ()
    revelation: Revelation | None = None


class OutlineChapterSubmission(BaseModel):
    number: int
    title: str
    arc_function: str
    beats: tuple[Beat, ...]
    assigned_elements: tuple[str, ...] = ()


class TreatmentException(BaseModel):
    a: str
    b: str
    treatment: Treatment


class StyleSheetSubmission(BaseModel):
    narrator: Narrator
    tense: Tense
    default_treatment: Treatment
    treatment_exceptions: tuple[TreatmentException, ...] = ()
    avoid_lexicon: tuple[str, ...] = ()


class PlanSubmission(BaseModel):
    world: WorldSubmission
    characters: tuple[InventedCharacter, ...] = ()
    places: tuple[InventedPlace, ...] = ()
    facts: tuple[InventedFact, ...] = ()
    chapters: tuple[OutlineChapterSubmission, ...]
    style_sheet: StyleSheetSubmission
    title: str


# Campos narrativos para el hook de policy (010-C09): todos los textos del plan salvo el léxico
# a evitar (`definitions.md` §7.5 — la política nunca escanea el léxico a evitar).
NARRATIVE_FIELDS: tuple[str, ...] = (
    "world.novum_description",
    "world.consequences[]",
    "characters[].name",
    "places[].name",
    "places[].description",
    "facts[].value",
    "chapters[].title",
    "chapters[].arc_function",
    "chapters[].beats[].description",
    "chapters[].beats[].events[].statement",
    "chapters[].beats[].revelation.theme",
    "chapters[].beats[].revelation.content",
    "title",
)

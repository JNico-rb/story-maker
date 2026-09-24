"""El testigo de un invariante violado, traducido a `Defecto` de `cronologia-lean` (§9.4).

Un defecto por invariante violado y por capítulo de los eventos de su testigo; sin capítulo (solo
eventos del brief), uno sin capítulo, que no es atribuible. El mensaje nombra el invariante, los
personajes y lugares del testigo por su nombre canónico y, de cada evento, su origen, su capítulo
y beat si los tiene y su momento real: los ids del testigo son los de las filas de la versión, así
que no hay nada que desplazar de vuelta. No evalúa ningún invariante (007-I1).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from story_maker.formal.result import INVARIANTS, ChronologyResult, Invariant
from story_maker.store.story_bible import EventEntry, StoryBible

VALIDATOR = "cronologia-lean"
MONTHS = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


@dataclass(frozen=True)
class Defect:
    """`Defecto` (`definitions.md` §6): atribuible si tiene capítulo."""

    validator: str
    criterion: str | None
    blocking: bool
    chapter: int | None
    message: str


def _when(moment: dt.datetime) -> str:
    return f"{moment.day} de {MONTHS[moment.month - 1]} de {moment.year} a las {moment:%H:%M}"


class _Describer:
    def __init__(self, bible: StoryBible) -> None:
        self.events = {e.id: e for e in bible.chronology.events}
        self.names = {c.id: c.canonical_name for c in bible.characters}
        self.places = {p.id: p.canonical_name for p in bible.places}

    def event(self, event: EventEntry) -> str:
        origin = "del brief" if event.origin == "brief" else "registrado"
        details = [_when(event.moment), f"en {self.places[event.place_id]}"]
        if event.chapter is not None:
            beat = f", beat {event.beat}" if event.beat is not None else ""
            details.insert(0, f"capítulo {event.chapter}{beat}")
        return f"el evento {origin} ({'; '.join(details)})"

    def explain(self, invariant: Invariant, w: tuple[int, ...]) -> tuple[str, list[EventEntry]]:
        """El mensaje del testigo `w` y los eventos que nombra."""
        match invariant:
            case "T1":
                before, after = self.events[w[0]], self.events[w[1]]
                return (
                    f"T1 · Orden temporal declarado: {self.event(after)} se narra después que "
                    f"{self.event(before)}, pero ocurre antes.",
                    [before, after],
                )
            case "T2":
                event = self.events[w[1]]
                return (
                    f"T2 · Edad coherente: en {self.event(event)}, {self.names[w[0]]} tiene "
                    f"{w[3]} años según su fecha de nacimiento, no los {w[2]} que se declaran.",
                    [event],
                )
            case "T3":
                first, second = self.events[w[1]], self.events[w[2]]
                return (
                    f"T3 · Nadie está en dos lugares a la vez: {self.names[w[0]]} está a la vez "
                    f"en {self.event(first)} y en {self.event(second)}.",
                    [first, second],
                )
            case "T4":
                exclusion, later = self.events[w[1]], self.events[w[2]]
                return (
                    f"T4 · Nadie vuelve de un evento excluyente: {self.names[w[0]]} sale de la "
                    f"historia en {self.event(exclusion)} y está presente en "
                    f"{self.event(later)}, posterior.",
                    [exclusion, later],
                )
            case "T5":
                event = self.events[w[1]]
                return (
                    f"T5 · Nadie actúa antes de nacer: {self.names[w[0]]} está presente en "
                    f"{self.event(event)}, anterior a su nacimiento.",
                    [event],
                )


def defects_from(result: ChronologyResult, bible: StoryBible) -> tuple[Defect, ...]:
    """Los defectos de un resultado `failed`, contra la story bible de la versión verificada."""
    if result.result != "failed":
        return ()
    describer = _Describer(bible)
    defects: list[Defect] = []
    for invariant in INVARIANTS:
        witness = result.witnesses.get(invariant)
        if witness is None:
            continue
        message, events = describer.explain(invariant, witness)
        chapters = sorted({e.chapter for e in events if e.chapter is not None})
        defects += [Defect(VALIDATOR, None, True, c, message) for c in chapters] or [
            Defect(VALIDATOR, None, True, None, message)
        ]
    return tuple(defects)

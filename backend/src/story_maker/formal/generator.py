"""Generador del `FicheroDeCronologia` (`architecture.md` §11.4).

El fichero lleva la cronología registrada (eventos de origen brief y registrados, nacimientos y
novum) y un teorema por invariante, que se cierra evaluando su comprobador. Va seudonimizado: ids
de fila y años desplazados 400·k.
"""

from __future__ import annotations

import datetime as dt
import secrets

from story_maker.formal.chronology import Chronology, ChronologyEvent, Presence

INVARIANTS = ("T1", "T2", "T3", "T4", "T5")

# Un ciclo gregoriano dura 400 años: desplazar 400·k conserva los bisiestos, y con ellos las
# edades y los cumpleaños. k > 0 para que el año nunca sea el real; k ≤ 10 para no salir del
# rango de fechas de Python (año 9999).
K_MIN, K_MAX = 1, 10


def _optional(value: int | None) -> str:
    return "none" if value is None else f"some {value}"


def _presence(presence: Presence) -> str:
    return f"⟨{presence.character_id}, {_optional(presence.declared_age)}⟩"


def _event(event: ChronologyEvent, years: int) -> str:
    m = event.moment
    kind = (
        f".excluyente {event.excluded_character_id}" if event.type == "exclusion" else ".ordinario"
    )
    presences = ", ".join(_presence(p) for p in event.presences)
    return (
        f"{{ id := {event.id}, momento := ⟨{m.year + years}, {m.month}, {m.day}, {m.hour}, "
        f"{m.minute}⟩, capitulo := {_optional(event.chapter)}, beat := {_optional(event.beat)}, "
        f"lugar := {event.place_id}, presentes := [{presences}], tipo := {kind}, "
        f"analepsis := {'true' if event.analepsis else 'false'} }}"
    )


def _date(date: dt.date, years: int) -> str:
    return f"⟨{date.year + years}, {date.month}, {date.day}⟩"


def _block(lines: list[str]) -> str:
    if not lines:
        return "[]"
    return "[\n" + ",\n".join(f"    {line}" for line in lines) + "\n  ]"


def generate_chronology_file(chronology: Chronology, k: int | None = None) -> str:
    """Fichero Lean de la cronología registrada; sin `k`, se elige al azar y no queda escrito."""
    if k is None:
        k = K_MIN + secrets.randbelow(K_MAX - K_MIN + 1)
    years = 400 * k
    events = [e for e in chronology.events if e.origin != "planned"]
    births = [
        f"⟨{c.id}, {_date(c.birth_date, years)}⟩"
        for c in chronology.characters
        if c.birth_date is not None
    ]
    theorems = "\n".join(
        f"theorem cumple{t} : {t} cronologia := "
        f"(compruebaT{t[1]}_decide cronologia).mp (by decide +kernel)"
        for t in INVARIANTS
    )
    audits = "\n".join(f"#print axioms cumple{t}" for t in INVARIANTS)
    return (
        "import Chronology\n\n"
        "open Chronology\n\n"
        "def cronologia : Cronologia where\n"
        f"  novum := {_date(chronology.novum_date, years)}\n"
        f"  nacimientos := {_block(births)}\n"
        f"  eventos := {_block([_event(e, years) for e in events])}\n\n"
        '#eval IO.println ("CRONOLOGIA-LEAN " ++ informe cronologia)\n\n'
        f"{theorems}\n\n"
        f"{audits}\n"
    )

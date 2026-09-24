"""La cronología registrada de una versión, leída de SQLite para el generador (§4.5, §11.4).

Solo pasan los ids de fila, los momentos, los números y los valores sí/no: los enunciados y los
nombres de la story bible se quedan en SQLite (007-I3). La lectura es la de la 009, que ya trae
solo los eventos de origen brief y registrados de esa versión (007-I6).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from story_maker.formal.chronology import (
    Chronology,
    ChronologyCharacter,
    ChronologyEvent,
    Presence,
)
from story_maker.store import story_bible
from story_maker.store.story_bible import EventEntry


def _event(entry: EventEntry) -> ChronologyEvent:
    return ChronologyEvent(
        id=entry.id,
        moment=entry.moment,
        place_id=entry.place_id,
        presences=tuple(Presence(p.character_id, p.declared_age) for p in entry.presences),
        type=entry.type,
        excluded_character_id=entry.excluded_character_id,
        analepsis=entry.analepsis,
        origin=entry.origin,
        chapter=entry.chapter,
        beat=entry.beat,
    )


def chronology_from(stored: story_bible.Chronology) -> Chronology:
    """La cronología de la 009 en la forma que lee el generador."""
    if stored.novum_date is None:
        raise LookupError("la versión no tiene mundo: su cronología no tiene fecha del novum")
    return Chronology(
        events=tuple(_event(e) for e in stored.events),
        characters=tuple(ChronologyCharacter(b.character_id, b.birth_date) for b in stored.births),
        novum_date=stored.novum_date,
    )


def chronology_of_version(session: Session, version_id: int) -> Chronology:
    return chronology_from(story_bible.read_chronology(session, version_id))

"""La plantilla de una CanonCard: el texto que el código escribe para una entidad y un capítulo
*d*, solo desde la story bible y en un orden que fija el contenido, nunca el id de las filas
(`architecture.md` §6.3)."""

from __future__ import annotations

from story_maker.retrieval.canon import WORLD, Canon, EntityKey, participation
from story_maker.store.story_bible import EventEntry, WorldEntry

TYPES = {"recipient": "destinatario", "close_one": "allegado", "invented": "inventado"}
SPECIES = {"person": "persona", "animal": "animal", "artificial": "artificial"}
SCOPES = {"technological": "tecnológico", "social": "social", "cognitive": "cognitivo"}


def render(canon: Canon, entity: EntityKey, chapter: int) -> str:
    """La tarjeta de `entity` en el capítulo `chapter`."""
    _, character_id, place_id = entity
    if character_id is not None:
        head = _character_head(canon, character_id)
    elif place_id is not None:
        head = _place_head(canon, place_id)
    else:
        head = _world_head(canon.bible.world)
    facts = sorted((f.attribute, f.value) for f in canon.facts_of(entity))
    lines = [*head, *_section("Hechos", [f"{a}: {v}" for a, v in facts])]
    if entity != WORLD:
        lines += _section("Eventos", _event_lines(canon, entity, chapter))
    return "\n".join(lines)


def _section(title: str, items: list[str]) -> list[str]:
    return [f"{title}:", *(f"- {item}" for item in items)] if items else []


def _character_head(canon: Canon, character_id: int) -> list[str]:
    character = next(c for c in canon.bible.characters if c.id == character_id)
    birth = f" Nacimiento: {character.birth_date.isoformat()}." if character.birth_date else ""
    return [
        f"Personaje: {character.canonical_name}",
        f"Tipo: {TYPES[character.type]}. Especie: {SPECIES[character.species]}.{birth}",
    ]


def _place_head(canon: Canon, place_id: int) -> list[str]:
    place = next(p for p in canon.bible.places if p.id == place_id)
    description = [f"Descripción: {place.description}"] if place.description else []
    return [f"Lugar: {place.canonical_name}", *description]


def _world_head(world: WorldEntry | None) -> list[str]:
    if world is None:
        raise LookupError("la versión no tiene mundo")
    return [
        "Mundo",
        f"Novum: {world.novum_description} (ámbito: {SCOPES[world.novum_scope]}; "
        f"fecha: {world.novum_date.isoformat()})",
        *_section("Consecuencias", list(world.consequences)),
    ]


def _event_lines(canon: Canon, entity: EntityKey, chapter: int) -> list[str]:
    """Los eventos de origen brief y los registrados antes de `chapter` en que participa la
    entidad; nunca los planificados."""
    events = [
        event
        for event in canon.bible.chronology.events
        if _known_before(event, chapter) and participation(event).includes(entity)
    ]
    return sorted(_event_line(canon, event) for event in events)


def _known_before(event: EventEntry, chapter: int) -> bool:
    if event.origin == "brief":
        return True
    return event.origin == "recorded" and event.chapter is not None and event.chapter < chapter


def _event_line(canon: Canon, event: EventEntry) -> str:
    present = sorted(canon.character_name(p.character_id) for p in event.presences)
    line = (
        f"{event.moment:%Y-%m-%d %H:%M}, en {canon.place_name(event.place_id)}; "
        f"presentes: {', '.join(present) or 'nadie'}; {event.statement}"
    )
    if event.excluded_character_id is not None:
        line += f"; excluyente, excluye a {canon.character_name(event.excluded_character_id)}"
    return line

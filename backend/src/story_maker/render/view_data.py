"""Ensambla `VersionViewData` desde SQLite para una `Version` — portada (`Novel`, `Brief`),
índice y capítulos (`Chapter`), ficha (`StoryBible` de 009) — sin traducir el repositorio de
009-story-bible-y-versiones a otra forma (013-C01 a 013-C05, 013-C14).

Una entidad de la ficha «aparece» en un capítulo por `UsoDeHecho` (ya resuelto en
`FactEntry.chapters`) o por un evento registrado en el que está presente (personaje) o que ocurre
en ella (lugar) — `definitions.md` §3 FichaDePersonajes.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from story_maker.render.version_view import CapituloVista, EntidadFicha, VersionViewData
from story_maker.store.models import Brief, Chapter, Novel, Version
from story_maker.store.story_bible import StoryBible, read_story_bible
from story_maker.store.versions import changed_chapters


def load_version_view_data(session: Session, version: Version) -> VersionViewData:
    novel = session.get(Novel, version.novel_id)
    if novel is None:
        raise LookupError(f"no existe la novela {version.novel_id}")

    bible = read_story_bible(session, version.id)
    chapters = (
        session.query(Chapter)
        .filter(Chapter.version_id == version.id)
        .order_by(Chapter.number)
        .all()
    )
    # Publicada: la lista congelada al publicar (`Version.changed_chapters`). Candidata: no hay
    # nada congelado todavía, se calcula contra su base (013-C04).
    changed = (
        list(version.changed_chapters)
        if version.status == "published"
        else changed_chapters(session, version)
    )

    return VersionViewData(
        title=novel.title or "",
        recipient=_recipient_name(bible),
        dedication=_dedication(session, novel.id),
        version_number=version.number,
        chapters=[CapituloVista(number=c.number, title=c.title, text=c.text) for c in chapters],
        changed_chapters=changed,
        ficha=_ficha(bible),
    )


def _recipient_name(bible: StoryBible) -> str:
    return next((c.canonical_name for c in bible.characters if c.type == "recipient"), "")


def _dedication(session: Session, novel_id: int) -> str:
    brief = session.query(Brief).filter(Brief.novel_id == novel_id).one_or_none()
    if brief is None or not isinstance(brief.content, dict):
        return ""
    return str(brief.content.get("dedication", ""))


def _ficha(bible: StoryBible) -> list[EntidadFicha]:
    characters = [
        EntidadFicha(
            name=c.canonical_name, kind="personaje", chapters=_character_chapters(bible, c.id)
        )
        for c in bible.characters
    ]
    places = [
        EntidadFicha(name=p.canonical_name, kind="lugar", chapters=_place_chapters(bible, p.id))
        for p in bible.places
    ]
    return characters + places


def _character_chapters(bible: StoryBible, character_id: int) -> list[int]:
    from_facts = {
        n for fact in bible.facts if fact.character_id == character_id for n in fact.chapters
    }
    from_events = {
        event.chapter
        for event in bible.chronology.events
        if event.chapter is not None
        and any(presence.character_id == character_id for presence in event.presences)
    }
    return sorted(from_facts | from_events)


def _place_chapters(bible: StoryBible, place_id: int) -> list[int]:
    from_facts = {n for fact in bible.facts if fact.place_id == place_id for n in fact.chapters}
    from_events = {
        event.chapter
        for event in bible.chronology.events
        if event.chapter is not None and event.place_id == place_id
    }
    return sorted(from_facts | from_events)

"""Aplica el plan aceptado a la story bible de la candidata, en una sola transacción
(010-C20..C23; `architecture.md` §5.4).

Mundo, reparto, lugares, hechos inventados, eventos planificados, el outline, la StyleSheet, el
título y las CanonCards iniciales nacen aquí; el punto de control 0 y el paso a `writing`
cierran la transacción. Lee la story bible inicial con el repositorio de 009
(`store.story_bible.read_story_bible`) para resolver los nombres del brief a sus ids; nunca
toca los personajes, lugares, hechos o eventos que ya existían (010-C20, última viñeta). El
texto, la huella y el índice de cada CanonCard son de 016; aquí solo nace con su
`desde_capitulo` (010-C22)."""

from __future__ import annotations

import datetime as dt
import hashlib

from sqlalchemy import or_

from story_maker.pipeline.planning.plan import Beat as PlanBeat
from story_maker.pipeline.planning.plan import PlannedEvent, PlanSubmission
from story_maker.store.models import (
    BannedTerm,
    CanonCard,
    Character,
    Checkpoint,
    Event,
    EventCharacter,
    Fact,
    Novel,
    OutlineChapter,
    Place,
    Run,
    StyleSheet,
    World,
)
from story_maker.store.session import UnitOfWork
from story_maker.store.story_bible import read_story_bible

CHILDREN_MAX_AGE = 11
TEEN_MAX_AGE = 17


def age_band(age: int) -> str:
    """`FranjaDeEdad` (`definitions.md` §1): infantil (<12), juvenil (12-17), adulto (18+)."""
    if age <= CHILDREN_MAX_AGE:
        return "children"
    if age <= TEEN_MAX_AGE:
        return "teen"
    return "adult"


def apply_accepted_plan(
    uow: UnitOfWork, run: Run, version_id: int, plan: PlanSubmission, *, now: dt.datetime
) -> None:
    """El plan aceptado, aplicado en una transacción; al salir, el punto de control 0 está
    escrito y la ejecución sigue en `writing` (010-C20)."""
    session = uow.session
    story_bible = read_story_bible(session, version_id)
    novel = session.get(Novel, run.novel_id)
    if novel is None:
        raise LookupError(f"no existe la novela {run.novel_id}")

    character_ids = {c.canonical_name: c.id for c in story_bible.characters}
    place_ids = {p.canonical_name: p.id for p in story_bible.places}
    brief_names = set(character_ids) | set(place_ids)
    recipient = next(c for c in story_bible.characters if c.type == "recipient")
    recipient_birth = recipient.birth_date or dt.date(story_bible.present_year - 18, 1, 1)
    recipient_age = story_bible.present_year - recipient_birth.year

    uow.add(
        World(
            version_id=version_id,
            novum_description=plan.world.novum_description,
            novum_scope=plan.world.novum_scope,
            novum_date=plan.world.novum_date,
            consequences=list(plan.world.consequences),
        )
    )

    for invented in plan.characters:
        character = Character(
            version_id=version_id,
            type="invented",
            species=invented.species,
            canonical_name=invented.name,
            birth_date=None,
            origin="invented",
        )
        uow.add(character)
        session.flush()
        character_ids[invented.name] = character.id

    for invented_place in plan.places:
        place = Place(
            version_id=version_id,
            canonical_name=invented_place.name,
            description=invented_place.description,
            origin="invented",
        )
        uow.add(place)
        session.flush()
        place_ids[invented_place.name] = place.id

    for invented_fact in plan.facts:
        subject_type, character_id, place_id = _subject(
            invented_fact.subject, character_ids, place_ids
        )
        uow.add(
            Fact(
                version_id=version_id,
                subject_type=subject_type,
                character_id=character_id,
                place_id=place_id,
                attribute=invented_fact.attribute,
                value=invented_fact.value,
                origin="invented",
                mandatory=False,
                personal_element_id=None,
            )
        )

    for chapter in plan.chapters:
        uow.add(
            OutlineChapter(
                version_id=version_id,
                number=chapter.number,
                title=chapter.title,
                arc_function=chapter.arc_function,
                beats=[_beat_json(beat) for beat in chapter.beats],
                assigned_elements=list(chapter.assigned_elements),
            )
        )
        for beat in chapter.beats:
            for event in beat.events:
                _add_planned_event(
                    uow, version_id, chapter.number, beat.number, event, character_ids, place_ids
                )

    uow.add(
        StyleSheet(
            version_id=version_id,
            content=_style_sheet_content(
                uow, plan, novel.user_id, run.novel_id, age_band(recipient_age)
            ),
        )
    )
    novel.title = plan.title

    for entity_type, name, character_id, place_id in _card_entities(character_ids, place_ids):
        # Del brief o el mundo: siempre 1. Inventado: el primer capítulo que lo nombra, o 1 si
        # ningún beat lo nombra (010-C22; `definitions.md` CanonCard).
        from_chapter = (
            1 if name in brief_names or entity_type == "world" else _from_chapter(name, plan)
        )
        text = f"{entity_type}:{name}"
        uow.add(
            CanonCard(
                version_id=version_id,
                entity_type=entity_type,
                character_id=character_id,
                place_id=place_id,
                from_chapter=from_chapter,
                text=text,
                content_hash=hashlib.sha256(text.encode()).hexdigest(),
            )
        )

    uow.add(Checkpoint(run_id=run.id, chapter=0, created_at=now))
    run.phase = "writing"
    run.chapter = 1


def _names_in_beat(beat: PlanBeat) -> set[str]:
    """Lo que un beat nombra (010-C22): sus personajes, los presentes/excluidos/lugares de sus
    eventos, y los sujetos de los hechos que usa se resuelven aparte (solo nombres aquí)."""
    names = set(beat.characters)
    for event in beat.events:
        names |= set(event.present)
        if event.excluded:
            names.add(event.excluded)
        names.add(event.place)
    return names


def _from_chapter(name: str, plan: PlanSubmission) -> int:
    for chapter in plan.chapters:
        for beat in chapter.beats:
            if name in _names_in_beat(beat):
                return chapter.number
    return 1


def _subject(
    subject: str, character_ids: dict[str, int], place_ids: dict[str, int]
) -> tuple[str, int | None, int | None]:
    if subject in character_ids:
        return "character", character_ids[subject], None
    if subject in place_ids:
        return "place", None, place_ids[subject]
    return "world", None, None


def _beat_json(beat: PlanBeat) -> dict[str, object]:
    """El JSON de `outline_chapters.beats` se copia tal cual entre versiones (009): sin ids de
    fila, solo lo que el plan entregó."""
    return {
        "number": beat.number,
        "description": beat.description,
        "characters": list(beat.characters),
        "facts_used": list(beat.facts_used),
        "revelation": (
            {"theme": beat.revelation.theme, "content": beat.revelation.content}
            if beat.revelation
            else None
        ),
        "events": [
            {
                "statement": e.statement,
                "moment": e.moment.isoformat(),
                "place": e.place,
                "type": e.type,
                "excluded": e.excluded,
                "analepsis": e.analepsis,
                "present": list(e.present),
            }
            for e in beat.events
        ],
    }


def _add_planned_event(
    uow: UnitOfWork,
    version_id: int,
    chapter_number: int,
    beat_number: int,
    event: PlannedEvent,
    character_ids: dict[str, int],
    place_ids: dict[str, int],
) -> None:
    row = Event(
        version_id=version_id,
        statement=event.statement,
        moment=event.moment,
        place_id=place_ids[event.place],
        type=event.type,
        excluded_character_id=character_ids[event.excluded] if event.excluded else None,
        analepsis=event.analepsis,
        origin="planned",
        chapter=chapter_number,
        beat=beat_number,
    )
    uow.add(row)
    uow.session.flush()
    for name in event.present:
        uow.add(EventCharacter(event_id=row.id, character_id=character_ids[name]))


def _card_entities(
    character_ids: dict[str, int], place_ids: dict[str, int]
) -> list[tuple[str, str, int | None, int | None]]:
    entities: list[tuple[str, str, int | None, int | None]] = [
        ("character", name, character_id, None) for name, character_id in character_ids.items()
    ]
    entities += [("place", name, None, place_id) for name, place_id in place_ids.items()]
    entities.append(("world", "__world__", None, None))
    return entities


def _style_sheet_content(
    uow: UnitOfWork, plan: PlanSubmission, user_id: int, novel_id: int, register: str
) -> dict[str, object]:
    """El léxico a evitar añade cada tema prohibido que aplica a la novela, en sus tres niveles
    (010-C21): una palabra no es un tema, así que la policy la caza, no esto (§7.5)."""
    topics = (
        uow.session.query(BannedTerm)
        .filter(
            BannedTerm.type == "topic",
            or_(
                BannedTerm.level == "global",
                (BannedTerm.level == "user") & (BannedTerm.user_id == user_id),
                (BannedTerm.level == "novel") & (BannedTerm.novel_id == novel_id),
            ),
        )
        .all()
    )
    avoid_lexicon: list[dict[str, object]] = [
        {"term": t, "keywords": []} for t in plan.style_sheet.avoid_lexicon
    ]
    avoid_lexicon += [
        {"term": topic.term, "keywords": list(topic.keywords or [])} for topic in topics
    ]
    return {
        "narrator": plan.style_sheet.narrator,
        "tense": plan.style_sheet.tense,
        "default_treatment": plan.style_sheet.default_treatment,
        "treatment_exceptions": [
            {"a": e.a, "b": e.b, "treatment": e.treatment}
            for e in plan.style_sheet.treatment_exceptions
        ],
        "register": register,
        "avoid_lexicon": avoid_lexicon,
    }

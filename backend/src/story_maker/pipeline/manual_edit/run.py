"""La ejecución `manual_edit`: revalida la base al arrancar y al relanzarse, crea la candidata por
copia, registra el capítulo editado sin writer, revisa los afectados por los hechos cambiados con
el writer en modo revisión y pasa el gate completo (`architecture.md` §9.1, §9.2, §10.3; 019-C18
a 019-C27).

Qué queda por hacer sale de los puntos de control: el del capítulo editado y el de cada afectado.
Los hechos cambiados son los de la candidata cuyo valor difiere del de la base: la copia conserva
el orden de las filas y una edición no crea hechos, así que emparejarlas por orden basta."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from story_maker.observability.port import Trace
from story_maker.pipeline.changes.affected import affected_chapters
from story_maker.pipeline.changes.run import REVISE_INSTRUCTION, revalidate_base
from story_maker.pipeline.manual_edit.edited import EditedChapter, edit_of_run
from story_maker.pipeline.production import ChapterProducer, Production, Revision
from story_maker.pipeline.runs import RunStop, get_run, naive
from story_maker.store.models import Character, Checkpoint, Fact, Place, Run
from story_maker.store.session import unit_of_work
from story_maker.store.version_copy import copy_version, rows_of_version


def start_edit(production: Production, run_id: int) -> None:
    """En una transacción: la candidata copiada de la base y el punto de control 0. Si falla, no
    queda nada y la ejecución cae con `crash`: al reanudar, revalida y la crea."""
    p = production
    try:
        with unit_of_work(p.session_factory) as uow:
            run = get_run(uow.session, run_id)
            if run.base_version_id is None:
                raise LookupError(f"la edición {run_id} no tiene versión base")
            copied = copy_version(uow, run.base_version_id, now=naive(p.clock()))
            run.candidate_version_id = copied.version.id
            run.phase, run.chapter = "writing", None
            uow.add(Checkpoint(run_id=run_id, chapter=0, created_at=naive(p.clock())))
    except Exception as exc:
        raise RunStop(
            "interrupted", "crash", f"falló la transacción de la candidata de la edición: {exc}"
        ) from exc


def changed_facts(session: Session, run: Run) -> list[tuple[Fact, Fact]]:
    """Pares (hecho de la base, hecho de la candidata) cuyo valor cambió."""
    if run.base_version_id is None or run.candidate_version_id is None:
        return []
    base = rows_of_version(session, Fact, run.base_version_id)
    candidate = rows_of_version(session, Fact, run.candidate_version_id)
    return [(old, new) for old, new in zip(base, candidate, strict=True) if old.value != new.value]


def _subject(session: Session, fact: Fact) -> str:
    if fact.character_id is not None:
        return session.get_one(Character, fact.character_id).canonical_name
    if fact.place_id is not None:
        return session.get_one(Place, fact.place_id).canonical_name
    return "el mundo"


def change_of(session: Session, run: Run) -> dict[str, Any]:
    """El cambio que reciben el writer y el editor de un afectado: los hechos cambiados ya
    validados, nunca el texto editado (019-I8)."""
    return {
        "changed_facts": [
            {
                "subject": _subject(session, old),
                "attribute": old.attribute,
                "old_value": old.value,
                "new_value": new.value,
            }
            for old, new in changed_facts(session, run)
        ],
        "new_fact": None,
    }


def affected_by_edit(session: Session, run: Run, edited: int) -> list[int]:
    """Como en 014, desde la base: los `UsoDeHecho` de los hechos cambiados y los capítulos con el
    valor antiguo literal, sin el editado."""
    changes = [(old.id, old.value) for old, _ in changed_facts(session, run)]
    if not changes:
        return []
    found = affected_chapters(session, run.base_version_id or 0, changes)
    return [chapter for chapter in found if chapter != edited]


def _checkpoints(session: Session, run_id: int) -> set[int]:
    rows = session.query(Checkpoint.chapter).filter(Checkpoint.run_id == run_id)
    return {row[0] for row in rows}


def _set_writing(production: Production, run_id: int, chapter: int) -> None:
    with unit_of_work(production.session_factory) as uow:
        run = get_run(uow.session, run_id)
        run.phase, run.chapter = "writing", chapter


async def write_edit(production: Production, run_id: int, trace: Trace) -> None:
    """Fase `writing`: el capítulo editado, sin writer, y después los afectados en orden
    ascendente con el writer en modo revisión; salta lo que ya tiene su punto de control."""
    p = production
    with p.session_factory() as session:
        if not _checkpoints(session, run_id):
            session.close()
            start_edit(p, run_id)
    with p.session_factory() as session:
        edited = edit_of_run(session, run_id).chapter
        done = _checkpoints(session, run_id)
    if edited not in done:
        _set_writing(p, run_id, edited)
        await EditedChapter(p).register(run_id, trace)
    with p.session_factory() as session:
        run = get_run(session, run_id)
        affected = affected_by_edit(session, run, edited)
        revision = Revision(change_of(session, run), REVISE_INSTRUCTION)
        done = _checkpoints(session, run_id)
    producer = ChapterProducer(p)
    for chapter in (c for c in affected if c not in done):
        _set_writing(p, run_id, chapter)
        await producer.produce_chapter(run_id, chapter, trace, revision=revision)


def revalidate_edit(production: Production, run_id: int) -> str | None:
    """Revalida la base; devuelve la fase en que sigue (`gate` si cayó en el gate)."""
    with unit_of_work(production.session_factory) as uow:
        run = get_run(uow.session, run_id)
        revalidate_base(uow.session, run)
        if run.phase in ("gate", "rewriting"):
            run.phase, run.chapter = "gate", None
        return run.phase

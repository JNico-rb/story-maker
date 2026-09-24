"""La ejecución de cambio: revalida la versión base, crea la candidata copiada y reescribe los
afectados antes del gate (`architecture.md` §9.1 `Regenerar`, §9.2, §10.1 «La ejecución de
cambio», §10.2; 014-C12 a 014-C18).

El orquestador la conduce; aquí están sus piezas: cada una lee y escribe en la unidad de trabajo
que se le da o en la suya, y termina la ejecución lanzando `RunStop`."""

from __future__ import annotations

from typing import Any, cast

from sqlalchemy.orm import Session

from story_maker.domain.constants import NAME
from story_maker.observability.port import Trace
from story_maker.pipeline.production import ChapterProducer, Production, Revision
from story_maker.pipeline.runs import RunStop, get_run, naive
from story_maker.store.models import (
    ChangeRequest,
    Character,
    Checkpoint,
    Fact,
    Place,
    Run,
)
from story_maker.store.session import UnitOfWork, unit_of_work
from story_maker.store.version_copy import VersionCopy, copy_version
from story_maker.store.versions import current_version

STALE_BASE = "stale_base"
REVISE_INSTRUCTION = (
    "Revisa el capítulo actual para que refleje el cambio: cambia solo lo mínimo que el cambio "
    "exige y conserva la continuidad con el resto de la novela."
)


def revalidate_base(session: Session, run: Run) -> None:
    """Solo sigue si su base es la versión vigente, al arrancar y al relanzarse (§10.2)."""
    current = current_version(session, run.novel_id)
    if current is None or current.id != run.base_version_id:
        vigente = f"v{current.number}" if current is not None else "ninguna"
        raise RunStop(
            "failed",
            STALE_BASE,
            f"la versión base {run.base_version_id} ya no es la vigente ({vigente})",
        )


def change_request_of(session: Session, run_id: int) -> ChangeRequest:
    return session.query(ChangeRequest).filter(ChangeRequest.run_id == run_id).one()


def start_change(production: Production, run_id: int) -> None:
    """En una transacción: la candidata copiada de la base, con los hechos aplicados y sus
    CanonCards, y el punto de control 0. Si falla, no queda nada y la ejecución cae con `crash`:
    al reanudar, revalida y la crea (014-C13)."""
    p = production
    try:
        with unit_of_work(p.session_factory) as uow:
            run = get_run(uow.session, run_id)
            if run.base_version_id is None:
                raise LookupError(f"la ejecución de cambio {run_id} no tiene versión base")
            proposal = cast(dict[str, Any], change_request_of(uow.session, run_id).proposal)
            copied = copy_version(uow, run.base_version_id, now=naive(p.clock()))
            apply_proposal(uow, copied, proposal)
            p.cards(uow, copied.version.id)
            run.candidate_version_id = copied.version.id
            run.phase, run.chapter = "writing", None
            uow.add(Checkpoint(run_id=run_id, chapter=0, created_at=naive(p.clock())))
    except Exception as exc:
        raise RunStop(
            "interrupted", "crash", f"falló la transacción de la candidata del cambio: {exc}"
        ) from exc


def apply_proposal(uow: UnitOfWork, copied: VersionCopy, proposal: dict[str, Any]) -> None:
    """Los valores nuevos en los hechos copiados (el de nombre cambia también el nombre canónico
    de su sujeto) y el hecho nuevo, de origen brief y no obligatorio (014-C13)."""
    session = uow.session
    for change in proposal.get("changes") or []:
        fact = session.get_one(Fact, copied.ids["facts"][change["fact_id"]])
        fact.value = change["new_value"]
        if fact.attribute == NAME:
            subject: Character | Place = (
                session.get_one(Character, fact.character_id)
                if fact.character_id is not None
                else session.get_one(Place, cast(int, fact.place_id))
            )
            subject.canonical_name = change["new_value"]
    new = proposal.get("new_fact")
    if new is not None:
        character = new["subject_type"] == "character"
        table = "characters" if character else "places"
        subject_id = copied.ids[table][new["subject_id"]]
        uow.add(
            Fact(
                version_id=copied.version.id,
                subject_type=new["subject_type"],
                character_id=subject_id if character else None,
                place_id=None if character else subject_id,
                attribute=new["attribute"],
                value=new["value"],
                origin="brief",
                mandatory=False,
            )
        )
    session.flush()


async def revise_affected(production: Production, run_id: int, trace: Trace, after: int) -> None:
    """Fase `writing`: los afectados posteriores al punto de control `after`, en orden
    ascendente, con el writer en modo revisión (014-C14, C18)."""
    p = production
    with p.session_factory() as session:
        request = change_request_of(session, run_id)
        affected = sorted(cast(list[int], request.affected_chapters or []))
        revision = Revision(change_of(session, request), REVISE_INSTRUCTION)
    producer = ChapterProducer(p)
    for chapter in (c for c in affected if c > after):
        with unit_of_work(p.session_factory) as uow:
            run = get_run(uow.session, run_id)
            run.phase, run.chapter = "writing", chapter
        await producer.produce_chapter(run_id, chapter, trace, revision=revision)


def change_of(session: Session, request: ChangeRequest) -> dict[str, Any]:
    """El cambio que reciben el writer y el editor: cada hecho con su sujeto, su valor antiguo y
    el nuevo, o el hecho nuevo; nunca la petición del cliente (014-I2)."""
    proposal = cast(dict[str, Any], request.proposal)
    changed = []
    for change in proposal.get("changes") or []:
        fact = session.get_one(Fact, change["fact_id"])
        changed.append(
            {
                "subject": _subject_name(session, fact.character_id, fact.place_id),
                "attribute": fact.attribute,
                "old_value": change["old_value"],
                "new_value": change["new_value"],
            }
        )
    new = proposal.get("new_fact")
    new_fact = None
    if new is not None:
        character = new["subject_type"] == "character"
        new_fact = {
            "subject": _subject_name(
                session,
                new["subject_id"] if character else None,
                None if character else new["subject_id"],
            ),
            "attribute": new["attribute"],
            "value": new["value"],
        }
    return {"changed_facts": changed, "new_fact": new_fact}


def _subject_name(session: Session, character_id: int | None, place_id: int | None) -> str:
    """El nombre canónico del sujeto en la versión base."""
    if character_id is not None:
        return session.get_one(Character, character_id).canonical_name
    return session.get_one(Place, cast(int, place_id)).canonical_name

"""Guardar una edición manual: 409 si la base ya no es la vigente; si no, en el acto la policy (con
audit log, origen `manual_edit`), `longitud-capitulo` y `nombres-exactos`. Si bloquean, 422 con
todos sus diagnósticos y nada creado; si pasan, la `EdicionManual` y su `Ejecucion` `manual_edit`
en cola (`architecture.md` §10.3, §12.2; 019-C10 a 019-C17, 019-I3, 019-I4).

La propiedad (404) la comprueba la ruta, como en el resto de la API (002)."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from story_maker.pipeline.manual_edit.checks import (
    active_banned,
    banned_diagnostics,
    name_variant_diagnostics,
)
from story_maker.pipeline.manual_edit.diagnostics import Diagnostic, ordered
from story_maker.pipeline.runs import naive
from story_maker.policy.audit import record_decision
from story_maker.policy.engine import decide
from story_maker.policy.types import CampoNarrativo, DecisionDePolitica, PeticionDePolitica
from story_maker.store.models import Character, ManualEdit, Novel, Run
from story_maker.store.session import unit_of_work
from story_maker.store.versions import current_version
from story_maker.validators.chapter_length import LENGTH, check_chapter_length
from story_maker.validators.exact_names import EXACT_NAMES

EDIT_LOCATION = "edición"
BANNED_TERMS = "palabras-prohibidas"
NO_PUBLISHED_VERSION = "la novela no tiene ninguna versión publicada"
STALE_BASE = "la versión base ya no es la vigente"


@dataclass(frozen=True)
class SaveRejected:
    status: int
    detail: Any


def edit_policy_request(
    user_id: int, novel_id: int, text: str, run_id: int | None = None
) -> PeticionDePolitica:
    return PeticionDePolitica(
        origen="manual_edit",
        cliente=str(user_id),
        novela=str(novel_id),
        ejecucion=str(run_id) if run_id is not None else None,
        campos=[CampoNarrativo(path=EDIT_LOCATION, texto=text, narrativo=True)],
    )


def judge_edit(
    session: Session, user_id: int, novel_id: int, text: str, run_id: int | None = None
) -> DecisionDePolitica:
    """La decisión del motor de 005 sobre el texto, con la ubicación de la coincidencia."""
    peticion = edit_policy_request(user_id, novel_id, text, run_id)
    entries = active_banned(session, user_id, novel_id)
    decision = decide(peticion.model_copy(update={"banned_entries": entries}))
    if decision.detail:
        located = [{**item, "location": EDIT_LOCATION} for item in decision.detail]
        decision = decision.model_copy(update={"detail": located})
    return decision


def blocking_diagnostics(
    session: Session, novel: Novel, version_id: int, text: str
) -> list[Diagnostic]:
    """Lo que bloquea el guardado: prohibidas, longitud y formas no canónicas, todas a la vez."""
    names = session.query(Character.canonical_name).filter(Character.version_id == version_id)
    found = [
        _validated(d, BANNED_TERMS)
        for d in banned_diagnostics(text, active_banned(session, novel.user_id, novel.id))
    ]
    length = check_chapter_length(text)
    found += [
        # La pantalla de 028 solo conoce los tipos del lint; `validator` dice cuál es.
        Diagnostic("linter", d.message, blocking=True, extra={"validator": LENGTH})
        for d in length.defects
    ]
    found += [
        _validated(d, EXACT_NAMES)
        for d in name_variant_diagnostics(text, [row[0] for row in names.order_by(Character.id)])
    ]
    return ordered(found)


def _validated(diagnostic: Diagnostic, validator: str) -> Diagnostic:
    return Diagnostic(
        diagnostic.type,
        diagnostic.message,
        diagnostic.blocking,
        diagnostic.start,
        diagnostic.end,
        {**diagnostic.extra, "validator": validator},
    )


def save_edit(
    session_factory: sessionmaker[Session],
    *,
    novel_id: int,
    chapter: int,
    text: str,
    base_version: int,
    now: dt.datetime,
) -> int | SaveRejected:
    """El id de la ejecución encolada, o por qué no se encola nada."""
    with unit_of_work(session_factory) as uow:
        session = uow.session
        novel = session.get_one(Novel, novel_id)
        current = current_version(session, novel_id)
        if current is None:
            return SaveRejected(409, NO_PUBLISHED_VERSION)
        if current.number != base_version:
            return SaveRejected(409, STALE_BASE)
        decision = judge_edit(session, novel.user_id, novel_id, text)
        record_decision(uow, edit_policy_request(novel.user_id, novel_id, text), decision)
        diagnostics = blocking_diagnostics(session, novel, current.id, text)
        if diagnostics:
            rejected = SaveRejected(422, {"diagnostics": [d.to_json() for d in diagnostics]})
        else:
            run = Run(
                novel_id=novel_id,
                type="manual_edit",
                status="queued",
                base_version_id=current.id,
                resumes=0,
                created_at=naive(now),
            )
            uow.add(run)
            session.flush()
            uow.add(
                ManualEdit(
                    novel_id=novel_id,
                    base_version_id=current.id,
                    chapter=chapter,
                    text=text,
                    status="queued",
                    run_id=run.id,
                    created_at=naive(now),
                )
            )
            return run.id
    return rejected

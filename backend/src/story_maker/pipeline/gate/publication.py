"""Transacción de publicación: la candidata que superó las cuatro etapas pasa a versión
(012-C23, 012-I3, 012-I4; `architecture.md` §9.3, §9.4).

Número, `published_at`, `changed_chapters` y ruta del PDF los pone `store.versions.publish`
(009); aquí se añaden, en la misma unidad de trabajo, la pasada aceptada, la ejecución
`published` y la solicitud de cambio o la edición manual `applied`. Todo o nada: quien llama
confirma o deshace la unidad entera."""

from __future__ import annotations

import datetime as dt

from story_maker.pipeline.runs import get_run, naive
from story_maker.store.models import Attempt, ChangeRequest, ManualEdit
from story_maker.store.session import UnitOfWork
from story_maker.store.versions import publish

GATE_EVALUABLE = "gate_cycle"


def record_pass(uow: UnitOfWork, run_id: int, cycle: int, outcome: str) -> None:
    """Una pasada con desenlace es un intento del evaluable `gate_cycle` (012-C21)."""
    uow.add(
        Attempt(
            run_id=run_id,
            evaluable=GATE_EVALUABLE,
            chapter=None,
            gate_cycle=cycle,
            number=cycle,
            outcome=outcome,
        )
    )


def mark_applied(uow: UnitOfWork, run_id: int) -> None:
    """La solicitud de cambio o la edición manual de la ejecución, si la hay, queda `applied`."""
    session = uow.session
    for request in session.query(ChangeRequest).filter(ChangeRequest.run_id == run_id):
        request.status = "applied"
    for edit in session.query(ManualEdit).filter(ManualEdit.run_id == run_id):
        edit.status = "applied"
    session.flush()


def publish_candidate(
    uow: UnitOfWork, *, run_id: int, cycle: int, pdf_path: str, now: dt.datetime
) -> None:
    run = get_run(uow.session, run_id)
    if run.candidate_version_id is None:
        raise LookupError(f"la ejecución {run_id} no tiene candidata")
    publish(uow, run.candidate_version_id, pdf_path=pdf_path, now=naive(now))
    record_pass(uow, run_id, cycle, "accept")
    run.status = "published"
    run.finished_at = naive(now)
    uow.session.flush()
    mark_applied(uow, run_id)

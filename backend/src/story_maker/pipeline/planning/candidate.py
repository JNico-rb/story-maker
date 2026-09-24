"""Arranca la fase `planning`: la candidata y el canon del brief, en una sola transacción
(010-C01..C05).

Llama al repositorio de 009 (`store.brief_canon.create_generation_candidate`); lo propio de la
010 es enlazar la candidata a la ejecución y, si algo falla, que la ejecución termine `failed`
con `internal_error` sin dejar rastro de la candidata a medio escribir."""

from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session, sessionmaker

from story_maker.store.brief_canon import ConfirmedBrief, create_generation_candidate
from story_maker.store.models import Run, Version
from story_maker.store.session import unit_of_work


def start_generation_phase(
    session_factory: sessionmaker[Session],
    run_id: int,
    novel_id: int,
    brief: ConfirmedBrief,
    *,
    now: dt.datetime,
) -> Version:
    """La candidata con el canon del brief, y la ejecución enlazada a ella en fase `planning`
    (010-C01). Si algo falla a mitad, nada de eso queda: la transacción entera se deshace y la
    ejecución termina `failed` con `internal_error`, en una transacción aparte."""
    try:
        with unit_of_work(session_factory) as uow:
            version = create_generation_candidate(uow, novel_id, brief, now=now)
            run = _run(uow.session, run_id)
            run.phase = "planning"
            run.candidate_version_id = version.id
        return version
    except Exception:
        with unit_of_work(session_factory) as uow:
            run = _run(uow.session, run_id)
            run.status = "failed"
            run.reason = "internal_error"
            run.finished_at = now
        raise


def _run(session: Session, run_id: int) -> Run:
    run = session.get(Run, run_id)
    if run is None:
        raise LookupError(f"no existe la ejecución {run_id}")
    return run

"""Lanzar una generación: la encola en la cola FIFO global, sin candidata; la crea al arrancar
(`architecture.md` §9.1 `Configurar`, §15.7; 011-C01, C02)."""

from __future__ import annotations

import datetime as dt

from story_maker.pipeline.runs import naive, queued_runs
from story_maker.store.models import Run
from story_maker.store.session import UnitOfWork


def enqueue_generation(uow: UnitOfWork, novel_id: int, *, now: dt.datetime) -> tuple[int, int]:
    """Devuelve el id de la ejecución y su posición en la cola."""
    run = Run(
        novel_id=novel_id,
        type="generation",
        status="queued",
        phase=None,
        chapter=None,
        resumes=0,
        created_at=naive(now),
    )
    uow.add(run)
    uow.session.flush()
    return run.id, [r.id for r in queued_runs(uow.session)].index(run.id) + 1

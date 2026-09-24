"""Lanzar una generación: la encola en la cola FIFO global, sin candidata; la crea al arrancar
(`architecture.md` §9.1 `Configurar`, §15.7; 011-C01, C02)."""

from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from story_maker.pipeline.runs import naive, queued_runs
from story_maker.store.models import Brief, Run, Version
from story_maker.store.session import UnitOfWork

UNFINISHED = ("queued", "running", "interrupted")


class LaunchRejected(ValueError):
    """La novela no está lista para una generación (011-C02)."""


def launch_obstacle(session: Session, novel_id: int) -> str | None:
    """Por qué no se puede lanzar la generación, o nada si la novela está lista: brief
    confirmado, ninguna versión publicada y ninguna generación sin terminar (§9.3)."""
    brief = session.query(Brief).filter(Brief.novel_id == novel_id).one_or_none()
    if brief is None or brief.status != "confirmed":
        return "el brief no está confirmado"
    published = session.query(Version).filter(
        Version.novel_id == novel_id, Version.status == "published"
    )
    if published.first() is not None:
        return "la novela ya tiene una versión publicada"
    unfinished = session.query(Run).filter(
        Run.novel_id == novel_id, Run.type == "generation", Run.status.in_(UNFINISHED)
    )
    if unfinished.first() is not None:
        return "la novela tiene una generación sin terminar"
    return None


def enqueue_generation(uow: UnitOfWork, novel_id: int, *, now: dt.datetime) -> tuple[int, int]:
    """Devuelve el id de la ejecución y su posición en la cola."""
    obstacle = launch_obstacle(uow.session, novel_id)
    if obstacle is not None:
        raise LaunchRejected(obstacle)
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

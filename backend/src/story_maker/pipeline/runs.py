"""Ciclo de vida de una `Ejecucion`: posición en la cola FIFO global, fallar, caer, reanudar y
el arranque del servidor (`architecture.md` §9.1 a §9.3; 011-C03, C06, C25, C26, C28).

Toda escritura pasa por la unidad de trabajo de quien llama; el reloj lo da quien llama."""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from typing import Literal

from sqlalchemy.orm import Session

from story_maker.store.models import ChangeRequest, ManualEdit, Run, Version
from story_maker.store.session import UnitOfWork
from story_maker.store.versions import discard

Clock = Callable[[], dt.datetime]
StopStatus = Literal["failed", "interrupted"]


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def naive(moment: dt.datetime) -> dt.datetime:
    """Como se guardan las fechas en SQLite: en UTC y sin huso."""
    if moment.tzinfo is None:
        return moment
    return moment.astimezone(dt.UTC).replace(tzinfo=None)


class RunStop(Exception):
    """Termina la ejecución en curso: `failed` o `interrupted`, con su motivo y su detalle."""

    def __init__(self, status: StopStatus, reason: str, detail: str) -> None:
        super().__init__(f"{status} ({reason}): {detail}")
        self.status: StopStatus = status
        self.reason = reason
        self.detail = detail


class ResumeRejected(ValueError):
    """Solo se reanuda una ejecución `interrupted` (§9.2)."""


def get_run(session: Session, run_id: int) -> Run:
    run = session.get(Run, run_id)
    if run is None:
        raise LookupError(f"no existe la ejecución {run_id}")
    return run


def queued_runs(session: Session) -> list[Run]:
    """Las `queued` de todo el servidor por fecha de creación; a igual fecha, por id."""
    return list(
        session.query(Run).filter(Run.status == "queued").order_by(Run.created_at, Run.id).all()
    )


def queue_position(session: Session, run: Run) -> int | None:
    """Posición desde 1 entre las `queued`; ninguna si no está en cola."""
    if run.status != "queued":
        return None
    return [r.id for r in queued_runs(session)].index(run.id) + 1


def running_run(session: Session) -> Run | None:
    return session.query(Run).filter(Run.status == "running").first()


def fail_run(uow: UnitOfWork, run_id: int, reason: str, detail: str, *, now: dt.datetime) -> Run:
    """`failed` con motivo, detalle y fecha de fin; su candidata, si existe, queda descartada, y su
    solicitud de cambio o su edición manual, si la tiene, `rejected` (§10.1, §10.3)."""
    run = get_run(uow.session, run_id)
    run.status = "failed"
    run.reason = reason
    run.reason_detail = detail
    run.finished_at = naive(now)
    if run.candidate_version_id is not None:
        candidate = uow.session.get(Version, run.candidate_version_id)
        if candidate is not None and candidate.status == "candidate":
            discard(uow, candidate.id)
    for request in uow.session.query(ChangeRequest).filter(ChangeRequest.run_id == run_id):
        request.status = "rejected"
    for edit in uow.session.query(ManualEdit).filter(ManualEdit.run_id == run_id):
        edit.status = "rejected"
    uow.session.flush()
    return run


def interrupt_run(
    uow: UnitOfWork, run_id: int, reason: str, detail: str, *, max_resumes: int, now: dt.datetime
) -> Run:
    """Caer: `interrupted` y reanudable, o `failed` con `resumes_exhausted` si ya no le quedan
    reanudaciones (011-C28). La candidata se conserva para reanudar."""
    run = get_run(uow.session, run_id)
    if run.resumes >= max_resumes:
        return fail_run(
            uow,
            run_id,
            "resumes_exhausted",
            f"cayó ({reason}: {detail}) con {run.resumes} reanudaciones de {max_resumes}",
            now=now,
        )
    run.status = "interrupted"
    run.reason = reason
    run.reason_detail = detail
    uow.session.flush()
    return run


def stop_run(
    uow: UnitOfWork, run_id: int, stop: RunStop, *, max_resumes: int, now: dt.datetime
) -> Run:
    if stop.status == "failed":
        return fail_run(uow, run_id, stop.reason, stop.detail, now=now)
    return interrupt_run(uow, run_id, stop.reason, stop.detail, max_resumes=max_resumes, now=now)


def resume_run(uow: UnitOfWork, run_id: int) -> int:
    """`interrupted` → `queued` en su puesto original (conserva su fecha de creación) y suma una
    reanudación; devuelve su posición en la cola (011-C26)."""
    run = get_run(uow.session, run_id)
    if run.status != "interrupted":
        raise ResumeRejected(
            f"la ejecución {run_id} está {run.status}: solo se reanuda interrupted"
        )
    run.status = "queued"
    run.resumes += 1
    run.reason = None
    run.reason_detail = None
    uow.session.flush()
    return [r.id for r in queued_runs(uow.session)].index(run.id) + 1


def interrupt_running_at_startup(
    uow: UnitOfWork, *, max_resumes: int, now: dt.datetime
) -> list[int]:
    """Al arrancar el servidor, lo que estaba `running` cae con `crash` (011-C25)."""
    running = uow.session.query(Run).filter(Run.status == "running").order_by(Run.id).all()
    for run in running:
        interrupt_run(
            uow,
            run.id,
            "crash",
            "el servidor se detuvo con la ejecución en curso",
            max_resumes=max_resumes,
            now=now,
        )
    return [run.id for run in running]

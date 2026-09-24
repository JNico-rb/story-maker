"""La ejecución de cambio: revalida la versión base, crea la candidata copiada y reescribe los
afectados antes del gate (`architecture.md` §9.1 `Regenerar`, §9.2, §10.1 «La ejecución de
cambio», §10.2; 014-C12 a 014-C18).

El orquestador la conduce; aquí están sus piezas: cada una lee y escribe en la unidad de trabajo
que se le da o en la suya, y termina la ejecución lanzando `RunStop`."""

from __future__ import annotations

from sqlalchemy.orm import Session

from story_maker.pipeline.production import Production
from story_maker.pipeline.runs import RunStop, get_run, naive
from story_maker.store.models import Checkpoint, Run
from story_maker.store.session import unit_of_work
from story_maker.store.version_copy import copy_version
from story_maker.store.versions import current_version

STALE_BASE = "stale_base"


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


def start_change(production: Production, run_id: int) -> None:
    """En una transacción: la candidata copiada de la base y el punto de control 0."""
    p = production
    with unit_of_work(p.session_factory) as uow:
        run = get_run(uow.session, run_id)
        if run.base_version_id is None:
            raise LookupError(f"la ejecución de cambio {run_id} no tiene versión base")
        candidate = copy_version(uow, run.base_version_id, now=naive(p.clock())).version
        run.candidate_version_id = candidate.id
        run.phase, run.chapter = "writing", None
        uow.add(Checkpoint(run_id=run_id, chapter=0, created_at=naive(p.clock())))

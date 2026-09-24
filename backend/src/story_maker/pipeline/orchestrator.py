"""Orquestador de una ejecución de generación: sigue desde su último punto de control
(`architecture.md` §9.1, §9.2; 011-C05, C23, C27).

- Sin punto de control: fase `planning`, que es de 010 (costura `planning`).
- Con el k de 0 a 9: fase `writing` desde el capítulo k+1, sin planner.
- Con el 10, o caída en `gate` o `rewriting`: fase `gate`, que es de 012 (costura `gate`).

Una fase termina la ejecución lanzando `RunStop`; el orquestador la deja `failed` (descartando la
candidata) o `interrupted`. Otra excepción la recibe el worker (`internal_error`)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from sqlalchemy.orm import Session

from story_maker.agents.ceiling import NeverFits
from story_maker.observability.port import Trace
from story_maker.pipeline.production import ChapterProducer, Production
from story_maker.pipeline.runs import RunStop, fail_run, get_run, stop_run
from story_maker.store.models import Checkpoint
from story_maker.store.session import unit_of_work

# Recibe el id de la ejecución y su traza; termina con la fase cumplida o lanza `RunStop`.
PhaseSeam = Callable[[int, Trace], Awaitable[None]]

TRACE_NAMES = {
    "generation": "generacion",
    "change_request": "solicitud-de-cambio",
    "manual_edit": "edicion-manual",
}


def last_checkpoint(session: Session, run_id: int) -> int | None:
    rows = session.query(Checkpoint.chapter).filter(Checkpoint.run_id == run_id)
    chapters = [row[0] for row in rows]
    return max(chapters) if chapters else None


@dataclass(frozen=True)
class Orchestrator:
    production: Production
    planning: PhaseSeam
    gate: PhaseSeam

    async def execute(self, run_id: int) -> None:
        """Lleva la ejecución `running` hasta que sale de `running` o hasta la costura del gate."""
        p = self.production
        with p.session_factory() as session:
            run = get_run(session, run_id)
            key, name, novel = f"run:{run.id}", TRACE_NAMES[run.type], str(run.novel_id)
        try:
            with p.telemetry.trace(key, name=name, session=novel) as trace:
                await self._advance(run_id, trace)
        except RunStop as stop:
            with unit_of_work(p.session_factory) as uow:
                stop_run(uow, run_id, stop, max_resumes=p.config.max_resumes, now=p.clock())
        except NeverFits as exc:
            with unit_of_work(p.session_factory) as uow:
                fail_run(uow, run_id, "infeasible_config", str(exc), now=p.clock())

    async def _advance(self, run_id: int, trace: Trace) -> None:
        p = self.production
        with unit_of_work(p.session_factory) as uow:
            run = get_run(uow.session, run_id)
            last = last_checkpoint(uow.session, run_id)
            if run.phase in ("gate", "rewriting") or last == 10:
                run.phase, run.chapter = "gate", None
            elif last is None:
                run.phase, run.chapter = "planning", None
            phase = run.phase
        if phase == "gate":
            await self.gate(run_id, trace)
            return
        if last is None:
            await self.planning(run_id, trace)
            with p.session_factory() as session:
                if get_run(session, run_id).status != "running":
                    return
                last = last_checkpoint(session, run_id)
            if last is None:
                raise RuntimeError("la planificación terminó sin el punto de control 0")
        await ChapterProducer(p).produce(run_id, trace, last + 1)
        await self.gate(run_id, trace)

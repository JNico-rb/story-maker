"""Worker: una tarea asyncio del mismo proceso que toma de la cola FIFO global la primera
ejecución `queued` y la lleva hasta que sale de `running`; nunca hay dos `running`
(`architecture.md` §9.1; 011-C03, C25, C29, I1)."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Awaitable, Callable

from sqlalchemy.orm import Session, sessionmaker

from story_maker.pipeline.runs import (
    Clock,
    fail_run,
    get_run,
    interrupt_running_at_startup,
    queued_runs,
    running_run,
)
from story_maker.store.session import unit_of_work

Execute = Callable[[int], Awaitable[None]]


class Worker:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        execute: Execute,
        *,
        max_resumes: int,
        clock: Clock,
        poll_seconds: float = 1.0,
    ) -> None:
        self._session_factory = session_factory
        self._execute = execute
        self._max_resumes = max_resumes
        self._clock = clock
        self._poll_seconds = poll_seconds
        self._wake = asyncio.Event()

    def recover(self) -> list[int]:
        """Al arrancar el servidor: lo que estaba `running` cae con `crash` (011-C25)."""
        with unit_of_work(self._session_factory) as uow:
            return interrupt_running_at_startup(
                uow, max_resumes=self._max_resumes, now=self._clock()
            )

    def _take_first(self) -> int | None:
        with unit_of_work(self._session_factory) as uow:
            if running_run(uow.session) is not None:
                return None
            queued = queued_runs(uow.session)
            if not queued:
                return None
            queued[0].status = "running"
            return queued[0].id

    async def run_next(self) -> int | None:
        """Toma la primera `queued` si no hay ninguna `running` y la lleva hasta el final.
        Una excepción imprevista la deja `failed` con `internal_error` (011-C29)."""
        run_id = self._take_first()
        if run_id is None:
            return None
        try:
            await self._execute(run_id)
        except Exception as exc:
            with unit_of_work(self._session_factory) as uow:
                if get_run(uow.session, run_id).status == "running":
                    fail_run(uow, run_id, "internal_error", repr(exc), now=self._clock())
        return run_id

    def notify(self) -> None:
        """Algo entró en la cola: despierta al worker antes de su sondeo."""
        self._wake.set()

    async def run_forever(self) -> None:
        """Arranque y bucle: la CLI (`resume`) encola desde otro proceso, así que además de
        `notify()` el worker consulta la cola cada `poll_seconds`."""
        self.recover()
        while True:
            if await self.run_next() is not None:
                continue
            self._wake.clear()
            with contextlib.suppress(TimeoutError):
                async with asyncio.timeout(self._poll_seconds):
                    await self._wake.wait()

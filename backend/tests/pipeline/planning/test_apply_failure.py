"""La transacción de aplicación falla (010-C23): con parte del plan ya escrita, nada de eso
queda, el intento aceptado no cuenta, y la ejecución termina `failed` con `internal_error` con
la candidata descartada."""

from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.planning.test_candidate import reference_brief
from tests.validators.test_outline import reference_plan

from story_maker.observability.null import NullObservability
from story_maker.observability.port import Trace
from story_maker.pipeline.planning import phase as phase_module
from story_maker.pipeline.planning.attempts import PlanAttemptOutcome
from story_maker.pipeline.planning.candidate import start_generation_phase
from story_maker.pipeline.planning.phase import finalize_accepted_plan
from story_maker.store.models import Attempt, Checkpoint, Run, ValidatorResult, Version, World

NOW = dt.datetime(2026, 9, 24, 12, 0)


async def test_a_fault_mid_application_leaves_nothing_and_fails_the_run(
    session_factory: sessionmaker[Session],
    run_id: int,
    novel_id: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = start_generation_phase(session_factory, run_id, novel_id, reference_brief(), now=NOW)

    def failing_apply(
        uow: object, run: object, version_id: int, plan: object, *, now: object
    ) -> None:
        world = World(
            version_id=version_id,
            novum_description="x",
            novum_scope="technological",
            novum_date=dt.date(2020, 1, 1),
            consequences=["a", "b"],
        )
        uow.add(world)  # type: ignore[attr-defined]
        uow.session.flush()  # type: ignore[attr-defined]
        raise RuntimeError("fallo inyectado a mitad de la aplicación")

    monkeypatch.setattr(phase_module, "apply_accepted_plan", failing_apply)

    outcome = PlanAttemptOutcome("accept", (), reference_plan(), attempt_number=1)

    with pytest.raises(RuntimeError):
        finalize_accepted_plan(
            session_factory,
            NullObservability(),
            Trace(key="run:1"),
            run_id,
            version.id,
            outcome,
            now=NOW,
        )

    with session_factory() as session:
        assert session.query(World).filter_by(version_id=version.id).count() == 0
        assert session.scalars(select(Attempt)).all() == []
        assert session.scalars(select(ValidatorResult)).all() == []
        assert session.scalars(select(Checkpoint).filter_by(run_id=run_id)).all() == []

        run = session.get(Run, run_id)
        assert run is not None
        assert (run.status, run.reason) == ("failed", "internal_error")

        candidate = session.get(Version, version.id)
        assert candidate is not None
        assert candidate.status == "discarded"

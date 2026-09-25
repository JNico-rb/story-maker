"""012-C8 · Lean y el juez corren a la vez."""

from __future__ import annotations

import asyncio
import dataclasses
from typing import Any

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed
from tests.pipeline.gate.conftest import (
    GateKit,
    evaluation,
    gate_passes,
    script_judges,
    script_rewrites,
    seed_t1_witness_in_6,
)

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import FakeAgent, FakeSession
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.formal.candidate import CandidateVerification
from story_maker.formal.result import INVARIANTS, ChronologyResult
from story_maker.observability.port import Trace

# Lo que espera cada doble a que el otro empiece; secuenciales, la etapa 2 no terminaría.
WAIT_SECONDS = 2


def test_lean_and_the_judge_start_without_waiting_for_each_other_and_stage_2_combines_both(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    port: AgentPort,
    ceiling: TokenCeiling,
    kit: GateKit,
    trace: Trace,
) -> None:
    before, after = seed_t1_witness_in_6(session_factory, at_gate)
    holds = {t: t != "T1" for t in INVARIANTS}
    kit.lean.outcomes.append(ChronologyResult("failed", holds, {"T1": (before, after)}))
    script_judges(fake, evaluation({"continuidad": 2}, {"continuidad": (4,)}), evaluation())
    script_rewrites(fake, 2)

    lean_started, judge_started = asyncio.Event(), asyncio.Event()
    judge_requests: list[SessionRequest] = []
    in_use_while_lean_runs: list[int] = []
    open_session = fake.open

    def open_waiting(request: SessionRequest, *args: Any) -> FakeSession:
        session = open_session(request, *args)
        if request.role != "judge" or judge_requests:
            return session
        judge_requests.append(request)
        judge_started.set()
        run = session.run

        async def run_after_lean_started() -> None:
            await asyncio.wait_for(lean_started.wait(), WAIT_SECONDS)
            await run()

        session.run = run_after_lean_started  # type: ignore[method-assign]
        return session

    fake.open = open_waiting  # type: ignore[method-assign]

    async def lean_after_judge_started(run_id: int) -> CandidateVerification:
        lean_started.set()
        await asyncio.wait_for(judge_started.wait(), WAIT_SECONDS)
        in_use_while_lean_runs.append(ceiling.in_use)
        return await kit.lean(run_id)

    gate = dataclasses.replace(kit.gate, lean=lean_after_judge_started)

    asyncio.run(gate(at_gate.run_id, trace))

    # el juez reserva lo suyo en el techo; el verificador, nada
    [judge] = judge_requests
    assert in_use_while_lean_runs[0] == port.reservation(judge)
    # decide con los defectos de los dos: el 4 (juez) y el 6 (Lean) en el mismo ciclo
    writers = [s.request.chapter for s in fake.sessions if s.request.role == "writer"]
    assert writers == [4, 6]
    assert gate_passes(session_factory, at_gate.run_id) == [(1, "rewrite"), (2, "accept")]

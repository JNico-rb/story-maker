"""012-C12 · Una interrupción en la etapa 2 no gasta la pasada."""

from __future__ import annotations

import asyncio
import dataclasses

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import USAGE, Seed
from tests.pipeline.gate.conftest import (
    PASSED,
    GateKit,
    chapter_hashes,
    evaluation,
    gate_passes,
    results,
    script_judges,
    version_of,
)

from story_maker.agents.fake import Fail, FakeAgent, Script
from story_maker.formal.candidate import CandidateVerification
from story_maker.formal.result import VerifierInterruption
from story_maker.observability.port import Trace
from story_maker.pipeline.runs import RunStop
from story_maker.store.models import RoleSession


def _judge_sessions(session_factory: sessionmaker[Session], run_id: int) -> list[str]:
    with session_factory() as session:
        rows = session.query(RoleSession).filter(
            RoleSession.run_id == run_id, RoleSession.role == "judge"
        )
        return [row.outcome for row in rows]


def _validators(session_factory: sessionmaker[Session], run_id: int) -> set[str]:
    return {r.validator for r in results(session_factory, run_id)}


def _assert_nothing_spent(
    session_factory: sessionmaker[Session],
    seed: Seed,
    fake: FakeAgent,
    kit: GateKit,
    before: dict[int, str],
) -> None:
    assert gate_passes(session_factory, seed.run_id) == []
    assert [s.request.role for s in fake.sessions] == ["judge"]
    assert kit.visual.calls == []
    assert kit.pdf.calls == []
    assert version_of(session_factory, seed.version_id).status == "candidate"
    assert chapter_hashes(session_factory, seed.version_id) == before


@pytest.mark.parametrize("reason", ["verifier_unreachable", "verifier_timeout"])
def test_an_unreachable_or_timed_out_verifier_interrupts_without_spending_the_pass(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
    reason: str,
) -> None:
    kit.lean.outcomes.append(VerifierInterruption(reason))  # type: ignore[arg-type]
    script_judges(fake, evaluation())
    before = chapter_hashes(session_factory, at_gate.version_id)

    with pytest.raises(RunStop) as stop:
        asyncio.run(kit.gate(at_gate.run_id, trace))

    assert (stop.value.status, stop.value.reason) == ("interrupted", reason)
    _assert_nothing_spent(session_factory, at_gate, fake, kit, before)
    # el juez terminó: su resultado queda guardado y su sesión, en `role_sessions`
    assert _validators(session_factory, at_gate.run_id) >= {"juez-novela"}
    assert _judge_sessions(session_factory, at_gate.run_id) == ["completed"]
    assert "cronologia-lean" not in _validators(session_factory, at_gate.run_id)
    assert not any(s.name.startswith("cronologia-lean") for s in trace.scores)


def test_a_provider_failure_of_the_judge_interrupts_and_waits_for_lean_to_finish(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    fake.script("judge", None, Script(steps=(Fail(result=True),), usage=USAGE))
    before = chapter_hashes(session_factory, at_gate.version_id)
    judge_done_before_lean: list[bool] = []

    async def slow_lean(run_id: int) -> CandidateVerification:
        await asyncio.sleep(0.05)
        judge_done_before_lean.append(fake.sessions[0].final is not None)
        kit.lean.outcomes.append(PASSED)
        return await kit.lean(run_id)

    gate = dataclasses.replace(kit.gate, lean=slow_lean)

    with pytest.raises(RunStop) as stop:
        asyncio.run(gate(at_gate.run_id, trace))

    assert (stop.value.status, stop.value.reason) == ("interrupted", "provider_error")
    _assert_nothing_spent(session_factory, at_gate, fake, kit, before)
    assert judge_done_before_lean == [True]
    assert "cronologia-lean" in _validators(session_factory, at_gate.run_id)
    assert _judge_sessions(session_factory, at_gate.run_id) == ["infrastructure_failure"]

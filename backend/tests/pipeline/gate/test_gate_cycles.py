"""012-C21 · Agotados los ciclos del gate, la ejecución falla (`max_retries.gate_cycles` = 2)."""

from __future__ import annotations

import asyncio

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed
from tests.pipeline.gate.conftest import (
    GateKit,
    evaluation,
    gate_passes,
    results,
    run_of,
    script_judges,
    script_rewrites,
    visual_defects,
    with_gate_cycles,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Trace


def _writers(fake: FakeAgent) -> list[int | None]:
    return [s.request.chapter for s in fake.sessions if s.request.role == "writer"]


def test_after_the_last_cycle_a_pass_with_blocking_defects_continues_and_publishes_with_its_defects(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    """Cambio de producto (2026-09-26): agotados los ciclos, la pasada con bloqueantes atribuibles
    sigue en vez de fallar, y la candidata se publica con sus defectos."""
    kit.visual.outcomes.extend(visual_defects(3) for _ in range(4))
    script_judges(fake, *(evaluation() for _ in range(4)))
    script_rewrites(fake, 3)

    asyncio.run(kit.gate(at_gate.run_id, trace))

    assert gate_passes(session_factory, at_gate.run_id) == [
        (1, "rewrite"),
        (2, "rewrite"),
        (3, "accept"),
    ]
    assert _writers(fake) == [3, 3]
    assert kit.visual.calls == [at_gate.run_id] * 3
    assert run_of(session_factory, at_gate.run_id).status == "published"


def test_a_third_pass_that_passes_publishes(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    kit.visual.outcomes.extend([visual_defects(3), visual_defects(3)])
    script_judges(fake, evaluation(), evaluation(), evaluation())
    script_rewrites(fake, 2)

    asyncio.run(kit.gate(at_gate.run_id, trace))

    assert gate_passes(session_factory, at_gate.run_id) == [
        (1, "rewrite"),
        (2, "rewrite"),
        (3, "accept"),
    ]
    assert run_of(session_factory, at_gate.run_id).status == "published"


def test_a_blocking_criterion_cited_on_several_chapters_leaves_its_comment_once_in_the_detail(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    """Bug de la tanda D (ejecución 16): el comentario del juez salía repetido una vez por cada
    capítulo citado (012-bug-D1)."""
    script_judges(
        fake, evaluation(scores={"continuidad": 2}, chapters={"continuidad": (1, 2, 3, 4, 5, 6)})
    )
    gate = with_gate_cycles(kit, 0)

    asyncio.run(gate(at_gate.run_id, trace))

    assert gate_passes(session_factory, at_gate.run_id) == [(1, "accept")]
    judge = next(
        r for r in results(session_factory, at_gate.run_id) if r.validator == "juez-novela"
    )
    assert judge.detail["comment"].count("justificación de continuidad") == 1


def test_with_zero_gate_cycles_the_first_pass_with_attributable_defects_continues_and_publishes(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    """Cambio de producto (2026-09-26): sin ciclos, la pasada con un defecto atribuible sigue en
    vez de fallar, y publica sin reescribir nada."""
    kit.visual.outcomes.append(visual_defects(3))
    script_judges(fake, evaluation())
    gate = with_gate_cycles(kit, 0)

    asyncio.run(gate(at_gate.run_id, trace))

    assert gate_passes(session_factory, at_gate.run_id) == [(1, "accept")]
    assert _writers(fake) == []
    assert run_of(session_factory, at_gate.run_id).status == "published"

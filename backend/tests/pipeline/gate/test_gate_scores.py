"""012-C24 · Cada validador del gate deja su resultado y su score."""

from __future__ import annotations

import asyncio
from typing import Any, cast

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed
from tests.pipeline.gate.conftest import (
    RUBRIC,
    STAGE_1,
    GateKit,
    append_to_chapter,
    evaluation,
    results,
    script_judges,
    with_gate_cycles,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Score, Span, Trace
from story_maker.pipeline.runs import RunStop
from story_maker.store.models import BannedTerm, ValidatorResult

GATE_VALIDATORS = {*STAGE_1, "cronologia-lean", "juez-novela", "pdf-enlaces"}


class ResultFirstObservability(NullObservability):
    """El doble nulo, anotando si el resultado del validador ya estaba guardado al llegar su
    score."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        super().__init__()
        self.session_factory = session_factory
        self.stored_before: dict[str, bool] = {}

    def score(
        self,
        trace: Trace,
        name: str,
        value: float,
        comment: str | None = None,
        span: Span | None = None,
    ) -> Score:
        validator = name.split("/")[0]
        if validator in GATE_VALIDATORS:
            with self.session_factory() as session:
                stored = session.query(ValidatorResult).filter(
                    ValidatorResult.validator == validator, ValidatorResult.chapter.is_(None)
                )
                self.stored_before.setdefault(name, stored.count() > 0)
        return super().score(trace, name, value, comment, span)


@pytest.fixture
def telemetry(session_factory: sessionmaker[Session]) -> ResultFirstObservability:
    return ResultFirstObservability(session_factory)


def _scores(trace: Trace) -> dict[str, Score]:
    return {s.name: s for s in trace.scores}


def _span_name(score: Score) -> str | None:
    return score.span.name if score.span is not None else None


def test_each_gate_validator_leaves_its_result_and_then_its_score_in_its_span(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
    telemetry: ResultFirstObservability,
) -> None:
    script_judges(fake, evaluation(4))

    asyncio.run(kit.gate(at_gate.run_id, trace))

    rows = results(session_factory, at_gate.run_id)
    assert {r.validator for r in rows} == GATE_VALIDATORS
    for row in rows:
        assert (row.run_id, row.version_id, row.passed, row.score) == (
            at_gate.run_id,
            at_gate.version_id,
            True,
            1.0,
        )
        assert cast(dict[str, Any], row.detail)["defects"] == []
    scores = _scores(trace)
    for name in GATE_VALIDATORS:
        assert scores[name].value == 1
        assert _span_name(scores[name]) == f"validador:{name}"
    for invariant in ("T1", "T2", "T3", "T4", "T5"):
        assert scores[f"cronologia-lean/{invariant}"].value == 1
    for criterion in RUBRIC:
        part = scores[f"juez-novela/{criterion}"]
        assert (part.value, part.comment) == (4, f"justificación de {criterion}")
        assert _span_name(part) == "validador:juez-novela"
    assert telemetry.stored_before
    assert all(telemetry.stored_before.values())


def test_a_failing_pass_also_sends_its_scores_with_the_chapter_of_each_defect_in_the_detail(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    low = evaluation({"continuidad": 2, "ritmo": 2}, {"continuidad": (4, 7), "ritmo": (9,)})
    script_judges(fake, low)

    with pytest.raises(RunStop):
        asyncio.run(with_gate_cycles(kit, 0)(at_gate.run_id, trace))

    judge = next(
        r for r in results(session_factory, at_gate.run_id) if r.validator == "juez-novela"
    )
    assert (judge.passed, judge.score) == (False, 0.0)
    defects = cast(dict[str, Any], judge.detail)["defects"]
    assert [(d["criterion"], d["chapter"], d["blocking"]) for d in defects] == [
        ("continuidad", 4, True),
        ("continuidad", 7, True),
        ("ritmo", 9, False),
    ]
    scores = _scores(trace)
    assert scores["juez-novela"].value == 0
    assert scores["juez-novela/continuidad"].value == 2
    assert scores["cronologia-lean"].value == 1


def test_the_banned_terms_score_names_the_term_the_level_and_the_variant(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
) -> None:
    with session_factory() as session:
        session.add(
            BannedTerm(
                level="user",
                user_id=at_gate.user_id,
                term="tormenta",
                type="word",
                normalized="tormenta",
            )
        )
        session.commit()
    append_to_chapter(session_factory, at_gate.version_id, 4, "Hubo tormentas.")

    with pytest.raises(RunStop):
        asyncio.run(with_gate_cycles(kit, 0)(at_gate.run_id, trace))

    score = _scores(trace)["palabras-prohibidas"]
    assert score.value == 0
    assert score.comment is not None
    for part in ("tormenta", "user", "tormentas"):
        assert part in score.comment
    banned = next(
        r for r in results(session_factory, at_gate.run_id) if r.validator == "palabras-prohibidas"
    )
    assert [d["chapter"] for d in cast(dict[str, Any], banned.detail)["defects"]] == [4]

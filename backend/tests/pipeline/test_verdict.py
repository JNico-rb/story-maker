"""El veredicto lo decide el código (011-C16; `verification.md` §5 C.3)."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    CRITERIA,
    Seed,
    chapter_call,
    editor_script,
    review,
    writer_script,
)

from story_maker.agents.fake import FakeAgent
from story_maker.config import Config
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Trace
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import ChapterProducer, verdict
from story_maker.store.models import Run, ValidatorResult
from story_maker.validators.chapter_rubric import ChapterReview, judge_review


def scores(**overrides: int) -> dict[str, int]:
    base = dict.fromkeys(CRITERIA, 4)
    base.update({k.replace("_", "-"): v for k, v in overrides.items()})
    return base


def blocking_in(criterion: str) -> dict[str, Any]:
    return {"criterion": criterion, "blocking": True, "message": f"falla {criterion}"}


ROWS = [
    ("todos 4, sin defectos", 1, scores(), [], "accept"),
    (
        "fidelidad-canon 2 y el resto 5",
        1,
        {**dict.fromkeys(CRITERIA, 5), "fidelidad-canon": 2},
        [],
        "rewrite",
    ),
    ("cumple-beats igual al umbral", 1, scores(cumple_beats=3), [], "accept"),
    (
        "personalización, prosa y tono 1",
        1,
        scores(fidelidad_canon=5, cumple_beats=5, personalizacion_natural=1, prosa=1, tono=1),
        [],
        "accept",
    ),
    ("bloqueante marcado en prosa", 1, scores(prosa=3), [blocking_in("prosa")], "accept"),
    (
        "bloqueante marcado en fidelidad-canon con 4",
        1,
        scores(),
        [blocking_in("fidelidad-canon")],
        "rewrite",
    ),
    ("3 de 3 con fidelidad-canon 2", 3, scores(fidelidad_canon=2), [], "fail"),
]


@pytest.mark.parametrize(("row", "attempt", "given", "defects", "expected"), ROWS)
def test_the_verdict_of_each_attempt_follows_the_table(
    row: str,
    attempt: int,
    given: dict[str, int],
    defects: list[dict[str, Any]],
    expected: str,
    config: Config,
) -> None:
    submitted = ChapterReview.model_validate(review(given, defects=defects))

    judgement = judge_review(submitted, config.thresholds)

    assert verdict(judgement.passed, attempt, max_attempts=3) == expected
    again = judge_review(
        ChapterReview.model_validate(review(given, defects=defects)), config.thresholds
    )
    assert again == judgement


def test_criteria_below_threshold_that_do_not_block_become_non_blocking_defects(
    config: Config,
) -> None:
    given = scores(fidelidad_canon=5, cumple_beats=5, personalizacion_natural=1, prosa=1, tono=1)

    judgement = judge_review(ChapterReview.model_validate(review(given)), config.thresholds)

    assert judgement.passed
    assert [(d.criterion, d.blocking) for d in judgement.defects] == [
        ("personalizacion-natural", False),
        ("prosa", False),
        ("tono", False),
    ]


def test_a_blocking_mark_on_a_non_blocking_criterion_counts_as_non_blocking(
    config: Config,
) -> None:
    submitted = ChapterReview.model_validate(review(scores(), defects=[blocking_in("prosa")]))

    judgement = judge_review(submitted, config.thresholds)

    assert [(d.criterion, d.blocking) for d in judgement.defects] == [("prosa", False)]


async def test_non_blocking_defects_of_an_accepted_chapter_go_to_the_report_and_langfuse(
    producer: ChapterProducer,
    fake: FakeAgent,
    telemetry: NullObservability,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    given = scores(fidelidad_canon=5, cumple_beats=5, personalizacion_natural=1, prosa=1, tono=1)
    fake.script("writer", "write", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(review(given)))

    await producer.produce_chapter(seed.run_id, 4, trace)

    with session_factory() as session:
        rubric = session.query(ValidatorResult).filter_by(validator="rubrica-capitulo").one()
        assert rubric.passed is True
        assert [(d["criterion"], d["blocking"]) for d in rubric.detail["defects"]] == [
            ("personalizacion-natural", False),
            ("prosa", False),
            ("tono", False),
        ]
    (score,) = [s for s in trace.scores if s.name == "rubrica-capitulo"]
    assert score.value == 1
    assert score.comment is not None
    assert "justificación de prosa" in score.comment


async def test_the_third_attempt_with_blocking_defects_fails_with_retries_exhausted(
    orchestrator: Orchestrator,
    fake: FakeAgent,
    seed: Seed,
    session_factory: sessionmaker[Session],
) -> None:
    low = review(scores(fidelidad_canon=2))
    fake.script("writer", "write", writer_script(chapter_call()))
    fake.script("writer", "rewrite", writer_script(chapter_call()))
    fake.script("writer", "rewrite", writer_script(chapter_call()))
    for _ in range(3):
        fake.script("editor", None, editor_script(low))

    await orchestrator.execute(seed.run_id)

    with session_factory() as session:
        run = session.get(Run, seed.run_id)
        assert run is not None
        assert (run.status, run.reason) == ("failed", "retries_exhausted")

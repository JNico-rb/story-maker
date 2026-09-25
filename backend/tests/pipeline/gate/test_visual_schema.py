"""017-C12 · Una entrega fuera de schema vuelve al revisor."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed
from tests.pipeline.gate.visual import (
    EMPTY,
    faithful,
    job_of,
    make_settings,
    make_stage,
    reviewer_script,
    reviewer_sessions,
    seed_visual,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Trace
from story_maker.pipeline.production import Production
from story_maker.validators.visual_review import VisualReviewSubmission


def _without_ficha() -> dict[str, Any]:
    delivery = faithful()
    del delivery["ficha"]
    return delivery


def _chapter_without_number() -> dict[str, Any]:
    delivery = faithful()
    del delivery["capitulos"][2]["number"]
    return delivery


@pytest.mark.parametrize(
    "invalid", [_without_ficha(), _chapter_without_number()], ids=["sin-ficha", "sin-numero"]
)
def test_a_delivery_out_of_schema_goes_back_to_the_reviewer_and_only_the_valid_one_is_compared(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    trace: Trace,
    tmp_path: Path,
    invalid: dict[str, Any],
) -> None:
    seed_visual(session_factory, at_gate)
    fake.script("visual_reviewer", None, reviewer_script(invalid, faithful()))

    outcome = asyncio.run(make_stage(production, make_settings(tmp_path))(job_of(at_gate), trace))

    [session] = reviewer_sessions(fake)
    assert session.reads[0].startswith("Entrada inválida para submit_visual_review")
    assert session.reads[1] == "Entrega recibida."
    assert outcome.defects == ()
    assert outcome.failure is None


def test_an_empty_part_is_not_a_schema_error() -> None:
    assert VisualReviewSubmission.model_validate(EMPTY).ficha == []

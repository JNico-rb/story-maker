"""011-I5: ningún rol escribe canon. Las sesiones del writer y del editor no cambian la
candidata; solo la transacción de aceptación escribe (`Production._accept`,
`pipeline/acceptance.py`). Se compara la candidata entera antes y después de un capítulo cuyo
único intento se rechaza (`max_retries.chapter` = 0: un intento agota el capítulo), así que
nunca llega a aceptarse — cualquier diferencia solo podría venir de la sesión misma, no de la
transacción de aceptación, que no corre."""

from __future__ import annotations

import dataclasses

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed, chapter_call, editor_script, review, writer_script

from story_maker.agents.fake import FakeAgent
from story_maker.config import Config, load_config
from story_maker.observability.port import Trace
from story_maker.pipeline.production import ChapterProducer
from story_maker.pipeline.runs import RunStop
from story_maker.settings import ROOT
from story_maker.store.models import (
    CanonCard,
    Chapter,
    Character,
    Event,
    Fact,
    OutlineChapter,
    Place,
    StyleSheet,
    World,
)

MODELS = (Chapter, CanonCard, Character, Place, Fact, Event, OutlineChapter, StyleSheet, World)


@pytest.fixture
def config() -> Config:
    base = load_config(ROOT / "config.json")
    return dataclasses.replace(
        base,
        max_retries={**base.max_retries, "chapter": 0},  # un solo intento por capítulo
        thresholds=dict.fromkeys(base.thresholds, 3),
    )


def _row_fields(row: object) -> dict[str, object]:
    return {k: v for k, v in vars(row).items() if k != "_sa_instance_state"}


def _fingerprint(
    session_factory: sessionmaker[Session], version_id: int
) -> dict[str, list[dict[str, object]]]:
    with session_factory() as session:
        return {
            model.__tablename__: sorted(
                (
                    _row_fields(row)
                    for row in session.scalars(select(model).filter_by(version_id=version_id)).all()
                ),
                key=repr,
            )
            for model in MODELS
        }


async def test_the_candidate_is_unchanged_after_a_chapter_attempt_that_never_gets_accepted(
    producer: ChapterProducer,
    fake: FakeAgent,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    before = _fingerprint(session_factory, seed.version_id)

    fake.script("writer", "write", writer_script(chapter_call()))
    fake.script(
        "editor", None, editor_script(review(scores=2))
    )  # bloqueante: por debajo del umbral

    with pytest.raises(RunStop) as excinfo:
        await producer.produce_chapter(seed.run_id, 1, trace)
    assert (excinfo.value.status, excinfo.value.reason) == ("failed", "retries_exhausted")

    assert _fingerprint(session_factory, seed.version_id) == before

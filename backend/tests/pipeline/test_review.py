"""La revisión del editor tiene schema y solo cita lo que existe (011-C15, 011-I11)."""

from __future__ import annotations

import json
from collections.abc import Callable
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
from story_maker.observability.port import Trace
from story_maker.pipeline.production import ChapterProducer
from story_maker.store.models import Attempt, Event


def event(seed: Seed, **overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "statement": "Marta sube al faro con Toby",
        "moment": "2026-05-01T18:00:00",
        "place_id": seed.places["Faro de Cabo Mayor"],
        "present": [
            {"character_id": seed.characters["Marta"], "age": 40},
            {"character_id": seed.characters["Toby"]},
        ],
        "type": "ordinary",
        "excluded_character_id": None,
        "analepsis": False,
        "beat": 2,
    }
    base.update(overrides)
    return base


def without_criterion(seed: Seed) -> dict[str, Any]:
    given = review()
    given["scores"] = given["scores"][1:]
    return given


def score_six(seed: Seed) -> dict[str, Any]:
    return review({**dict.fromkeys(CRITERIA, 4), "prosa": 6})


INVALID: dict[str, Callable[[Seed], dict[str, Any]]] = {
    "falta un criterio": without_criterion,
    "una puntuación es 6": score_six,
    "personaje inexistente": lambda s: review(events=[event(s, present=[{"character_id": 999}])]),
    "lugar inexistente": lambda s: review(events=[event(s, place_id=999)]),
    "uso de algo que no es un hecho": lambda s: review(usages=[999]),
    "exclusion sin excluido": lambda s: review(events=[event(s, type="exclusion")]),
    "ordinary con excluido": lambda s: review(
        events=[event(s, excluded_character_id=s.characters["Toby"])]
    ),
    "beat fuera del capítulo": lambda s: review(events=[event(s, beat=7)]),
    "sin resumen": lambda s: review(summary=""),
}


def attempts(session_factory: sessionmaker[Session], run_id: int) -> list[Any]:
    with session_factory() as session:
        rows = session.query(Attempt).filter_by(run_id=run_id, chapter=4).order_by(Attempt.id)
        return [(a.number, a.outcome) for a in rows]


async def test_a_complete_review_that_cites_what_exists_is_valid(
    producer: ChapterProducer,
    fake: FakeAgent,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    valid = review(
        defects=[{"criterion": "prosa", "blocking": False, "message": "repite «faro»"}],
        usages=[seed.facts["rasgo"]],
        events=[event(seed)],
    )
    fake.script("writer", "write", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(valid))

    await producer.produce_chapter(seed.run_id, 4, trace)

    assert fake.sessions[1].reads == ["Entrega recibida."]
    assert attempts(session_factory, seed.run_id) == [(1, "accept")]


@pytest.mark.parametrize("row", list(INVALID))
async def test_an_invalid_review_returns_to_the_editor_and_does_not_count_as_an_attempt(
    row: str,
    producer: ChapterProducer,
    fake: FakeAgent,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    fake.script("writer", "write", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(INVALID[row](seed), review()))

    await producer.produce_chapter(seed.run_id, 4, trace)

    editor = fake.sessions[1]
    assert editor.request.role == "editor"
    assert editor.reads[0].startswith("Entrada inválida para submit_review")
    assert editor.reads[1] == "Entrega recibida."
    assert len(fake.sessions) == 2
    assert attempts(session_factory, seed.run_id) == [(1, "accept")]
    with session_factory() as session:
        assert session.query(Event).filter_by(origin="recorded").count() == 0


async def test_an_editor_session_without_a_valid_review_closes_the_attempt_without_accepting(
    producer: ChapterProducer,
    fake: FakeAgent,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    fake.script("writer", "write", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(review(usages=[999])))
    fake.script("writer", "rewrite", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(review()))

    await producer.produce_chapter(seed.run_id, 4, trace)

    assert [(s.request.role, s.request.mode) for s in fake.sessions] == [
        ("writer", "write"),
        ("editor", None),
        ("writer", "rewrite"),
        ("editor", None),
    ]
    rewrite = json.loads(fake.sessions[2].request.message)
    assert "defects" not in rewrite["call_inputs"]
    assert attempts(session_factory, seed.run_id) == [(1, "rewrite"), (2, "accept")]

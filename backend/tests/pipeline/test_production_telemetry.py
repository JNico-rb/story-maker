"""Trazas, spans y scores de la producción (011-C31)."""

from __future__ import annotations

import dataclasses
from typing import Any

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    CRITERIA,
    Seed,
    chapter_call,
    editor_script,
    review,
    writer_script,
)

from story_maker.agents.fake import Fail, FakeAgent, Script
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Score, Span, Trace
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import Production
from story_maker.pipeline.runs import resume_run
from story_maker.store.models import Chapter, Run, ValidatorResult
from story_maker.store.session import unit_of_work

VALIDATORS = ("longitud-capitulo", "nombres-exactos", "rubrica-capitulo")


class WatchedObservability(NullObservability):
    """Registra, con cada score, si el capítulo de su span ya está aceptado en la base."""

    def __init__(self, session_factory: sessionmaker[Session], version_id: int) -> None:
        super().__init__()
        self._session_factory = session_factory
        self._version_id = version_id
        self.emitted: list[tuple[str, str | None, bool]] = []

    def score(
        self,
        trace: Trace,
        name: str,
        value: float,
        comment: str | None = None,
        span: Span | None = None,
    ) -> Score:
        chapter = int(span.name.split("-")[1]) if span and span.name.startswith("capitulo-") else 0
        with self._session_factory() as session:
            accepted = (
                session.query(Chapter)
                .filter_by(version_id=self._version_id, number=chapter)
                .count()
                > 0
            )
        self.emitted.append((name, span.name if span else None, accepted))
        return super().score(trace, name, value, comment, span)


def accept_chapter(fake: FakeAgent, mode: str = "write") -> None:
    fake.script("writer", mode, writer_script(chapter_call()))
    fake.script("editor", None, editor_script(review()))


def role_spans(span: Span) -> list[str]:
    return [child.name for child in span.children if child.name.startswith("rol:")]


async def test_one_generation_trace_a_span_per_chapter_and_scores_per_validation(
    production: Production,
    planning: Any,
    gate: Any,
    fake: FakeAgent,
    seed: Seed,
    session_factory: sessionmaker[Session],
) -> None:
    telemetry = WatchedObservability(session_factory, seed.version_id)
    production = dataclasses.replace(production, telemetry=telemetry)
    orchestrator = Orchestrator(production=production, planning=planning, gate=gate)
    accept_chapter(fake)
    fake.script("writer", "write", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(review(dict.fromkeys(CRITERIA, 1))))
    accept_chapter(fake, "rewrite")
    fake.script("writer", "write", Script(steps=(Fail(result=True),)))

    await orchestrator.execute(seed.run_id)

    with session_factory() as session:
        assert session.get_one(Run, seed.run_id).status == "interrupted"
    with unit_of_work(session_factory) as uow:
        resume_run(uow, seed.run_id)
        uow.session.get_one(Run, seed.run_id).status = "running"
    for _ in range(3, 11):
        accept_chapter(fake)
    await orchestrator.execute(seed.run_id)

    assert list(telemetry.traces) == [f"run:{seed.run_id}"]
    trace = telemetry.traces[f"run:{seed.run_id}"]
    assert (trace.name, trace.session) == ("generacion", str(seed.novel_id))
    chapters = [s for s in trace.spans if s.name.startswith("capitulo-")]
    assert {s.name for s in chapters} == {f"capitulo-{n}" for n in range(1, 11)}
    (second,) = [s for s in chapters if s.name == "capitulo-2"]
    assert len(role_spans(second)) == 4  # writer y editor de los dos intentos
    for span in chapters:
        assert all(child.parent is span for child in span.children)

    names_2 = [
        s.name for s in trace.scores if s.span is second and s.name.split("/")[0] in VALIDATORS
    ]
    per_run = [*VALIDATORS, *(f"rubrica-capitulo/{c}" for c in CRITERIA)]
    assert names_2 == per_run + per_run
    length = next(s for s in trace.scores if s.name == "longitud-capitulo")
    assert length.value in (0, 1)
    assert length.comment is not None
    assert "1250 palabras" in length.comment
    criterion = next(s for s in trace.scores if s.name == "rubrica-capitulo/prosa")
    assert 1 <= criterion.value <= 5
    assert criterion.comment == "justificación de prosa"
    ours = [s for s in trace.scores if s.name.split("/")[0] in VALIDATORS]
    assert all(any(s.span is c for c in chapters) for s in ours)  # los de 003 y 005, aparte

    emitted_2 = [
        (name, accepted) for name, span, accepted in telemetry.emitted if span == "capitulo-2"
    ]
    assert [accepted for _, accepted in emitted_2] == [False] * len(per_run) + [True] * len(per_run)

    with session_factory() as session:
        rows = session.query(ValidatorResult).filter_by(run_id=seed.run_id, chapter=2)
        assert sorted((r.detail["attempt"], r.validator) for r in rows) == sorted(
            (attempt, v) for attempt in (1, 2) for v in VALIDATORS
        )

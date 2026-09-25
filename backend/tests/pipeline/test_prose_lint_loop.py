"""Los linters de prosa en el bucle del capítulo: su punto `editor` (018-C18 a 018-C23)."""

from __future__ import annotations

import json
from typing import Any

import pytest
from sqlalchemy import event as sa_event
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    BANNED,
    CRITERIA,
    Seed,
    chapter_call,
    editor_script,
    review,
    text_of,
    writer_script,
)

from story_maker.agents.fake import FakeAgent
from story_maker.lint.chapter import LINTERS
from story_maker.observability.port import Span, Trace
from story_maker.pipeline.production import ChapterProducer
from story_maker.pipeline.report import build_report
from story_maker.pipeline.runs import RunStop
from story_maker.store.models import Attempt, Checkpoint, Run, ValidatorResult

# Un párrafo que dispara los cuatro linters: «ventana» 3 veces (repetición), un cliché
# (estilo IA) y «me» en la narración con la StyleSheet en tercera persona (consistencia). El
# relleno sin signos da frases de 50 palabras: la legibilidad de la franja adulta avisa.
NOISY_OPENING = (
    "La ventana se abrió. La ventana crujió. La ventana cayó. "
    "Sin lugar a dudas era tarde. Aquella tarde me pareció eterna."
)


def noisy_text(words: int = 1200) -> str:
    return f"{NOISY_OPENING}\n\n{text_of(words)}"


def chapter_span(trace: Trace, chapter: int) -> Span:
    (span,) = [s for s in trace.spans if s.name == f"capitulo-{chapter}"]
    return span


def child_names(span: Span) -> list[str]:
    return [child.name for child in span.children]


def editor_inputs(fake: FakeAgent, index: int = -1) -> dict[str, Any]:
    editors = [s for s in fake.sessions if s.request.role == "editor"]
    return dict(json.loads(editors[index].request.message)["call_inputs"])


async def test_linters_run_after_the_hooks_and_before_the_editor_which_receives_their_warnings(
    producer: ChapterProducer, fake: FakeAgent, seed: Seed, trace: Trace
) -> None:
    fake.script("writer", "write", writer_script(chapter_call(text=noisy_text())))
    fake.script("editor", None, editor_script(review()))

    await producer.produce_chapter(seed.run_id, 4, trace)

    names = child_names(chapter_span(trace, 4))
    spans = [f"validador:{linter}" for linter in LINTERS]
    assert [n for n in names if n.startswith("validador:linter-")] == spans
    writer, editor = names.index("rol:writer"), names.index("rol:editor")
    assert all(writer < names.index(s) < editor for s in spans)
    warnings = editor_inputs(fake)["lint_defects"]
    assert [w["validator"] for w in warnings] == sorted(
        (w["validator"] for w in warnings), key=LINTERS.index
    )
    assert {w["validator"] for w in warnings} == set(LINTERS)
    assert all(w["blocking"] is False and w["criterion"] is None for w in warnings)


def all_spans(span: Span) -> list[Span]:
    return [span, *(s for child in span.children for s in all_spans(child))]


def linter_spans(trace: Trace) -> list[str]:
    return [
        s.name
        for top in trace.spans
        for s in all_spans(top)
        if s.name.startswith("validador:linter-")
    ]


@pytest.mark.parametrize(
    "rejected",
    [noisy_text(999 - len(NOISY_OPENING.split())), f"{noisy_text()} {BANNED}"],
    ids=["longitud", "prohibida"],
)
async def test_a_delivery_that_fails_the_hooks_never_reaches_the_linters(
    rejected: str, producer: ChapterProducer, fake: FakeAgent, seed: Seed, trace: Trace
) -> None:
    passing = text_of(1000)
    fake.script(
        "writer",
        "write",
        writer_script(chapter_call(text=rejected), chapter_call(text=passing)),
    )
    fake.script("editor", None, editor_script(review()))

    await producer.produce_chapter(seed.run_id, 4, trace)

    assert linter_spans(trace) == [f"validador:{linter}" for linter in LINTERS]
    warnings = editor_inputs(fake)["lint_defects"]
    assert warnings
    assert not any("ventana" in w["message"] for w in warnings)


def attempts(session_factory: sessionmaker[Session], run_id: int) -> list[tuple[int, str | None]]:
    with session_factory() as session:
        rows = session.query(Attempt).filter_by(run_id=run_id).order_by(Attempt.id)
        return [(a.number, a.outcome) for a in rows]


async def test_with_only_warnings_the_chapter_is_accepted_in_that_attempt(
    producer: ChapterProducer,
    fake: FakeAgent,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    fake.script("writer", "write", writer_script(chapter_call(text=noisy_text())))
    fake.script("editor", None, editor_script(review()))

    await producer.produce_chapter(seed.run_id, 4, trace)

    assert editor_inputs(fake)["lint_defects"]
    assert [s.request.role for s in fake.sessions] == ["writer", "editor"]
    assert attempts(session_factory, seed.run_id) == [(1, "accept")]


async def test_in_a_rewrite_for_another_cause_the_writer_receives_the_warnings(
    producer: ChapterProducer,
    fake: FakeAgent,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    low = review({**dict.fromkeys(CRITERIA, 4), "fidelidad-canon": 2})
    fake.script("writer", "write", writer_script(chapter_call(text=noisy_text())))
    fake.script("editor", None, editor_script(low))
    fake.script("writer", "rewrite", writer_script(chapter_call(text=text_of(1250))))
    fake.script("editor", None, editor_script(review()))

    await producer.produce_chapter(seed.run_id, 4, trace)

    first_warnings = editor_inputs(fake, 0)["lint_defects"]
    rewrite = fake.sessions[2]
    assert (rewrite.request.role, rewrite.request.mode) == ("writer", "rewrite")
    defects = json.loads(rewrite.request.message)["call_inputs"]["defects"]
    assert [(d["criterion"], d["blocking"]) for d in defects if d["validator"] not in LINTERS] == [
        ("fidelidad-canon", True)
    ]
    assert [d for d in defects if d["validator"] in LINTERS] == first_warnings
    assert linter_spans(trace) == [f"validador:{linter}" for linter in LINTERS] * 2
    second_warnings = editor_inputs(fake, 1)["lint_defects"]
    assert second_warnings
    assert not any("ventana" in w["message"] for w in second_warnings)
    assert attempts(session_factory, seed.run_id) == [(1, "rewrite"), (2, "accept")]


# Frases de 10 palabras de una sílaba: la legibilidad adulta, el estilo y la consistencia
# pasan; «sol» 50 veces por párrafo dispara solo `linter-repeticion`.
REPETITIVE = "\n\n".join(
    " ".join(["Sol sol sol sol sol sol sol sol sol sol."] * 5) for _ in range(25)
)


def lint_rows(session_factory: sessionmaker[Session], run_id: int) -> list[ValidatorResult]:
    with session_factory() as session:
        rows = (
            session.query(ValidatorResult)
            .filter(ValidatorResult.run_id == run_id, ValidatorResult.validator.in_(LINTERS))
            .order_by(ValidatorResult.id)
        )
        return list(rows)


async def test_with_the_acceptance_one_result_per_linter_in_sqlite_and_in_the_report(
    producer: ChapterProducer,
    fake: FakeAgent,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    fake.script("writer", "write", writer_script(chapter_call(text=REPETITIVE)))
    fake.script("editor", None, editor_script(review()))

    await producer.produce_chapter(seed.run_id, 4, trace)

    rows = lint_rows(session_factory, seed.run_id)
    assert [(r.validator, r.version_id, r.chapter, r.passed) for r in rows] == [
        ("linter-repeticion", seed.version_id, 4, False),
        ("linter-legibilidad", seed.version_id, 4, True),
        ("linter-estilo-ia", seed.version_id, 4, True),
        ("linter-consistencia", seed.version_id, 4, True),
    ]
    repetition, readability, ai_style, consistency = rows
    assert repetition.score == 25
    assert readability.score == 136.64
    assert (ai_style.score, consistency.score) == (0, 0)
    messages = [d["message"] for d in repetition.detail["defects"]]
    assert messages[0] == '"sol" 50 veces en el párrafo 1'
    assert len(messages) == 25
    assert all(r.detail["defects"] == [] for r in rows[1:])
    with session_factory() as session:
        report = build_report(session, session.get_one(Run, seed.run_id))
    unresolved = [d for d in report["unresolved"] if d["validator"] in LINTERS]
    assert [(d["chapter"], d["validator"], d["blocking"]) for d in unresolved] == [
        (4, "linter-repeticion", False)
    ] * 25


async def test_after_the_commit_one_score_per_linter_goes_to_langfuse(
    producer: ChapterProducer,
    fake: FakeAgent,
    seed: Seed,
    trace: Trace,
) -> None:
    fake.script("writer", "write", writer_script(chapter_call(text=REPETITIVE)))
    fake.script("editor", None, editor_script(review()))

    await producer.produce_chapter(seed.run_id, 4, trace)

    span = chapter_span(trace, 4)
    scores = [s for s in trace.scores if s.name in LINTERS]
    assert [(s.name, s.value, s.span) for s in scores] == [
        ("linter-repeticion", 25, span),
        ("linter-legibilidad", 136.64, span),
        ("linter-estilo-ia", 0, span),
        ("linter-consistencia", 0, span),
    ]
    comments = {s.name: s.comment for s in scores}
    assert comments["linter-repeticion"] == (
        "una palabra 3 veces o una muletilla 2 veces en un párrafo"
    )
    assert comments["linter-legibilidad"] == (
        "franja adult: longitud media de frase máxima 20; índice de Fernández-Huerta mínimo 60"
    )
    assert comments["linter-estilo-ia"] == "umbral 6 por 1.000 palabras; clichés encontrados: 0"
    assert comments["linter-consistencia"] == (
        "narrador en tercera persona; tratamientos admitidos: tú"
    )


async def test_a_failed_acceptance_transaction_sends_no_linter_score(
    producer: ChapterProducer,
    fake: FakeAgent,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    fake.script("writer", "write", writer_script(chapter_call(text=REPETITIVE)))
    fake.script("editor", None, editor_script(review()))

    def boom(*_: Any) -> None:
        raise RuntimeError("fallo provocado al escribir el punto de control")

    sa_event.listen(Checkpoint, "before_insert", boom)
    try:
        with pytest.raises(RunStop):
            await producer.produce_chapter(seed.run_id, 4, trace)
    finally:
        sa_event.remove(Checkpoint, "before_insert", boom)

    assert [s for s in trace.scores if s.name in LINTERS] == []
    assert lint_rows(session_factory, seed.run_id) == []

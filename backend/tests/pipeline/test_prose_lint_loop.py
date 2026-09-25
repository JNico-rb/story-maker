"""Los linters de prosa en el bucle del capítulo: su punto `editor` (018-C18 a 018-C23)."""

from __future__ import annotations

import json
from typing import Any

from tests.pipeline.conftest import (
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

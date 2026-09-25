"""Volver a registrar un capítulo tras un fallo de datos de `revision-visual`: el editor lo lee de
nuevo con el defecto como entrada y registra usos, eventos y resumen, sin writer; el texto y su
huella no cambian (`architecture.md` §9.4; 017-C17).

Re-registrar no reescribe: la revisión del editor sustituye lo registrado del capítulo con la
misma transacción de aceptación de 011 (`accept_chapter`), sin veredicto que pueda devolverlo al
writer. Una sesión sin revisión válida no registra nada: el ciclo siguiente repite el fallo y lo
acotan los ciclos del gate."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

from story_maker.agents.port import SessionRequest
from story_maker.observability.port import Trace
from story_maker.pipeline.acceptance import CHAPTER_EVALUABLE, accept_chapter
from story_maker.pipeline.production import Production, rubric_run
from story_maker.pipeline.runs import RunStop
from story_maker.pipeline.submissions import citable, submit_review_tool
from story_maker.pipeline.windows import editor_message
from story_maker.store.models import Attempt, Chapter
from story_maker.store.session import unit_of_work
from story_maker.validators.chapter_rubric import ChapterReview, judge_review


async def reregister_chapter(
    production: Production,
    *,
    run_id: int,
    user_id: int,
    novel_id: int,
    version_id: int,
    gate_cycle: int,
    chapter: int,
    defects: Sequence[Mapping[str, Any]],
    trace: Trace,
) -> None:
    p = production
    with p.telemetry.span(trace, f"capitulo-{chapter}") as span:
        with p.session_factory() as session:
            row = (
                session.query(Chapter)
                .filter(Chapter.version_id == version_id, Chapter.number == chapter)
                .one()
            )
            title, text, words = row.title, row.text, row.word_count
            known = citable(session, version_id, chapter)
            window = p.windows.editor(session, version_id, chapter, title, text)
        request = SessionRequest(
            role="editor",
            mode=None,
            user_id=user_id,
            novel_id=novel_id,
            prompt=p.prompts.editor,
            prompt_version=p.prompts.editor_version,
            message=editor_message(window, title, text, lint_defects=(), gate_defects=defects),
            tools=(submit_review_tool(known),),
            trace=trace,
            parent_span=span,
            run_id=run_id,
            chapter=chapter,
        )
        result = await p.port.run(request)
        if result.outcome == "infrastructure_failure":
            raise RunStop(
                "interrupted",
                "provider_error",
                f"capítulo {chapter}: la sesión del editor terminó por un error del proveedor",
            )
        if not result.deliveries:
            return
        review = cast(ChapterReview, result.deliveries[0].value)
        run = rubric_run(judge_review(review, p.config.thresholds))
        with unit_of_work(p.session_factory) as uow:
            attempt = 1 + (
                uow.session.query(Attempt)
                .filter(
                    Attempt.run_id == run_id,
                    Attempt.evaluable == CHAPTER_EVALUABLE,
                    Attempt.chapter == chapter,
                    Attempt.gate_cycle == gate_cycle,
                )
                .count()
            )
            accept_chapter(
                uow,
                run_id=run_id,
                version_id=version_id,
                chapter=chapter,
                title=title,
                text=text,
                word_count=words,
                review=review,
                attempt=attempt,
                runs=(run,),
                cards=p.cards,
                now=p.clock(),
                gate_cycle=gate_cycle,
            )

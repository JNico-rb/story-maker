"""La etapa 3 del `GateDePublicacion`: `revision-visual` sobre la `VistaDeVersion` de la
candidata (`architecture.md` §9.4, §11.2; spec 017)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy.orm import Session

from story_maker.agents.port import SessionRequest, SessionResult
from story_maker.observability.port import Span, Trace
from story_maker.pipeline.gate.phase import GateJob, VisualReviewOutcome
from story_maker.pipeline.production import Production
from story_maker.render.view_data import load_version_view_data
from story_maker.store.models import Version
from story_maker.validators.visual_review import (
    VALIDATOR,
    ExpectedChapter,
    ExpectedCover,
    ExpectedEntity,
    ExpectedStructure,
    reviewer_message,
    submit_visual_review_tool,
)


def expected_structure(session: Session, version_id: int) -> ExpectedStructure:
    """Lo que debe mostrar la vista de la candidata, con los mismos datos que la pinta (013):
    solo la candidata, nunca su base (017-C01)."""
    data = load_version_view_data(session, session.get_one(Version, version_id))
    chapters = tuple(ExpectedChapter(c.number, c.title, c.text) for c in data.chapters)
    return ExpectedStructure(
        cover=ExpectedCover(data.title, data.recipient, data.dedication),
        index=tuple(c.number for c in chapters),
        chapters=chapters,
        ficha=tuple(ExpectedEntity(e.name, e.kind, frozenset(e.chapters)) for e in data.ficha),
    )


ViewUrl = Callable[[int], str]


@dataclass(frozen=True)
class VisualReviewStage:
    """La etapa entera: comprobación de datos, sesión del revisor visual, comparación, resultado y
    scores. `view_url` da la dirección de la vista de una versión con su token de vista (013)."""

    production: Production
    view_url: ViewUrl
    prompt: str
    prompt_version: str | None = None

    async def __call__(self, job: GateJob, trace: Trace) -> VisualReviewOutcome:
        p = self.production
        with p.telemetry.span(trace, f"validador:{VALIDATOR}") as span:
            with p.session_factory() as session:
                expected = expected_structure(session, job.version_id)
            await self._review(job, expected, trace, span)
        return VisualReviewOutcome()

    async def _review(
        self, job: GateJob, expected: ExpectedStructure, trace: Trace, span: Span
    ) -> SessionResult:
        request = SessionRequest(
            role="visual_reviewer",
            mode=None,
            user_id=job.user_id,
            novel_id=job.novel_id,
            prompt=self.prompt,
            prompt_version=self.prompt_version,
            message=reviewer_message(self.view_url(job.version_id), expected),
            tools=(submit_visual_review_tool(),),
            trace=trace,
            parent_span=span,
            run_id=job.run_id,
        )
        return await self.production.port.run(request)

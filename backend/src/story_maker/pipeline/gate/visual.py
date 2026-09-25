"""La etapa 3 del `GateDePublicacion`: `revision-visual` sobre la `VistaDeVersion` de la
candidata (`architecture.md` §9.4, §11.2; spec 017)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from sqlalchemy.orm import Session

from story_maker.agents.port import SessionRequest, SessionResult
from story_maker.formal.defects import Defect
from story_maker.observability.port import Span, Trace
from story_maker.pipeline.gate.phase import GateJob, VisualReviewOutcome
from story_maker.pipeline.production import Production
from story_maker.pipeline.runs import naive
from story_maker.render.view_data import load_version_view_data
from story_maker.store.models import ValidatorResult, Version
from story_maker.store.session import unit_of_work
from story_maker.validators.visual_review import (
    VALIDATOR,
    ExpectedChapter,
    ExpectedCover,
    ExpectedEntity,
    ExpectedStructure,
    VisualDefect,
    VisualReviewSubmission,
    VisualVerdict,
    compare,
    data_defects,
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
            data = data_defects(expected)
            if data:
                # Es código y va antes: no se abre el revisor en este ciclo (017-C10).
                verdict = VisualVerdict((("ficha", False),), data)
                self._record(job, trace, span, verdict)
                return _outcome(verdict)
            result = await self._review(job, expected, trace, span)
            if result.outcome == "infrastructure_failure":
                # Infraestructura, no un intento (§7.6): no se compara nada (017-C15).
                return VisualReviewOutcome(
                    interruption="provider_error",
                    detail="la sesión del revisor visual cayó: el navegador (Playwright MCP) o "
                    f"el proveedor no respondieron ({result.error})",
                )
            if not result.deliveries:
                return VisualReviewOutcome(
                    no_valid_delivery=True,
                    detail=f"el revisor visual terminó sin entrega válida ({result.outcome})",
                )
            observed = cast(VisualReviewSubmission, result.deliveries[0].value)
            verdict = compare(expected, observed)
            self._record(job, trace, span, verdict)
        return _outcome(verdict)

    def _record(self, job: GateJob, trace: Trace, span: Span, verdict: VisualVerdict) -> None:
        """Primero el `ResultadoDeValidador`; una vez guardado, el score `revision-visual` y uno
        por parte evaluada, en el span del validador (017-C16)."""
        p = self.production
        by_part = {
            part: [d.message for d in verdict.defects if d.part == part]
            for part, _ in verdict.parts
        }
        comment = _messages([f"{d.part}: {d.message}" for d in verdict.defects])
        detail: dict[str, Any] = {
            "gate_cycle": job.cycle,
            "comment": comment,
            "parts": [{"name": part, "score": int(ok)} for part, ok in verdict.parts],
            "defects": [
                {
                    "validator": VALIDATOR,
                    "part": d.part,
                    "kind": d.kind,
                    "blocking": True,
                    "chapter": d.chapter,
                    "message": d.message,
                }
                for d in verdict.defects
            ],
        }
        with unit_of_work(p.session_factory) as uow:
            uow.add(
                ValidatorResult(
                    run_id=job.run_id,
                    version_id=job.version_id,
                    validator=VALIDATOR,
                    chapter=None,
                    passed=verdict.passed,
                    score=1.0 if verdict.passed else 0.0,
                    detail=detail,
                    created_at=naive(p.clock()),
                )
            )
        p.telemetry.score(trace, VALIDATOR, int(verdict.passed), comment, span)
        for part, ok in verdict.parts:
            p.telemetry.score(trace, f"{VALIDATOR}/{part}", int(ok), _messages(by_part[part]), span)

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


def _outcome(verdict: VisualVerdict) -> VisualReviewOutcome:
    """Lo que la etapa entrega al gate: pasa; fallo de datos atribuido; o no atribuible, si una
    entidad sin capítulo no sale en ninguno (solo el cliente puede arreglarlo, §9.4)."""
    defects = tuple(_gate_defect(d) for d in verdict.defects)
    witnesses = [
        f"{d.part}: {d.message}" for d in verdict.defects if d.kind == "datos" and d.chapter is None
    ]
    if witnesses:
        return VisualReviewOutcome(defects, "unattributable_defect", "; ".join(witnesses))
    if any(d.kind == "render" for d in verdict.defects):
        # Es código: ni se reescribe ni se vuelve a registrar nada (§9.4).
        return VisualReviewOutcome(defects, "render_failure", "; ".join(d.message for d in defects))
    return VisualReviewOutcome(defects=defects, reregister=bool(defects))


def _gate_defect(defect: VisualDefect) -> Defect:
    return Defect(VALIDATOR, defect.part, True, defect.chapter, f"{defect.part}: {defect.message}")


def _messages(messages: list[str]) -> str:
    return "; ".join(messages) or "sin defectos"

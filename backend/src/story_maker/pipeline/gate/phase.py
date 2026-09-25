"""`GateDePublicacion`: la costura `gate` del orquestador (011). Cada pasada recorre las cuatro
etapas en orden económico sobre la candidata tal como está, decide con la precedencia de 012-C17
y termina en publicación, reescritura dirigida, fallo o caída (`architecture.md` §9.1, §9.4;
012-C1, C2, C4, C7, C18 a C24).

- Una pasada con desenlace es un intento de `gate_cycle`; la que cortó una interrupción o una
  caída no cuenta, así que al reanudar se repite con el mismo número (012-C22).
- Las pasadas nunca superan 1 + `max_retries.gate_cycles` (012-I2): la última no reescribe.
- La reescritura rehace los capítulos atribuidos, por número y uno a uno, con el bucle de
  capítulo de 011 y los intentos contados dentro de su ciclo (012-C19, C20).

Las etapas 3 (`revision-visual`, 017) y 4 (PDF y `pdf-enlaces`, 013) llegan por costuras."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Any, cast

from story_maker.agents.port import SessionRequest
from story_maker.domain.constants import CHAPTERS_PER_NOVEL
from story_maker.domain.rubric import NOVEL_RUBRIC
from story_maker.formal.candidate import CandidateVerification
from story_maker.formal.defects import VALIDATOR as LEAN
from story_maker.formal.defects import Defect
from story_maker.formal.result import INVARIANTS, ChronologyResult, VerifierInterruption
from story_maker.observability.port import Span, Trace
from story_maker.pipeline.gate import inputs
from story_maker.pipeline.gate.precedence import PassVerdict, gate_precedence
from story_maker.pipeline.gate.publication import publish_candidate, record_pass
from story_maker.pipeline.gate.reregister import reregister_chapter
from story_maker.pipeline.production import ChapterProducer, Production, defect_entry
from story_maker.pipeline.runs import RunStop, get_run, naive
from story_maker.policy.audit import record_decision
from story_maker.policy.types import DecisionDePolitica, PeticionDePolitica
from story_maker.store.models import Attempt, Chapter, Novel, ValidatorResult
from story_maker.store.session import unit_of_work
from story_maker.store.story_bible import read_story_bible
from story_maker.validators.judge import VALIDATOR as JUDGE
from story_maker.validators.judge import JudgeEvaluation, judge_result, submit_evaluation_tool
from story_maker.validators.novel import (
    BANNED_TERMS_VALIDATOR,
    NovelValidatorResult,
    banned_terms_in_chapters,
    lean_stage_result,
    mandatory_elements_result,
)

PDF_LINKS = "pdf-enlaces"
GATE_EVALUABLE = "gate_cycle"


@dataclass(frozen=True)
class VisualReviewOutcome:
    """Lo que devuelve la etapa 3 (017): sus defectos atribuibles, o el motivo de un fallo no
    atribuible (`render_failure`). Sus resultados y scores los deja 017."""

    defects: tuple[Defect, ...] = ()
    failure: str | None = None
    detail: str = ""
    # Un fallo de datos: sus capítulos los vuelve a registrar el editor, sin writer (§9.4).
    reregister: bool = False
    # La sesión del revisor terminó sin entrega válida: ciclo fallido sin capítulos (017-C14).
    no_valid_delivery: bool = False
    # Infraestructura (el navegador o el proveedor): la ejecución pasa a `interrupted` (017-C15).
    interruption: str | None = None


@dataclass(frozen=True)
class PdfOutcome:
    """La etapa 4 (013): la ruta del PDF generado, o ninguna si no llegó a generarse, y si pasa
    `pdf-enlaces`."""

    path: str | None
    links_passed: bool = False
    detail: str = ""


LeanStage = Callable[[int], Awaitable[CandidateVerification]]
VisualReview = Callable[["GateJob", Trace], Awaitable[VisualReviewOutcome]]
PdfStage = Callable[[int], Awaitable[PdfOutcome]]


@dataclass(frozen=True)
class GateJob:
    run_id: int
    user_id: int
    novel_id: int
    version_id: int
    cycle: int
    cycles_remaining: bool


@dataclass(frozen=True)
class PassResult:
    verdict: PassVerdict
    defects: tuple[Defect, ...] = ()
    detail: str = ""
    pdf_path: str | None = None
    reregister: bool = False


@dataclass(frozen=True)
class _StageTwoPart:
    """Lo que aporta a la etapa 2 cada uno de sus dos validadores."""

    defects: tuple[Defect, ...] = ()
    unattributable: str | None = None
    interruption: str | None = None
    no_valid_delivery: bool = False
    detail: str = ""


@dataclass(frozen=True)
class JudgeRun:
    evaluation: JudgeEvaluation | None
    provider_error: bool


def _messages(defects: Sequence[Defect]) -> str:
    """El comentario de cada validador una sola vez: un defecto bloqueante atribuido a varios
    capítulos (el juez cita uno por criterio) repite el mismo mensaje, y no debe duplicarse en el
    detalle (012-bug-D1)."""
    return "; ".join(dict.fromkeys(d.message for d in defects)) or "sin defectos"


def _defect_detail(defect: Defect) -> dict[str, Any]:
    return {
        "validator": defect.validator,
        "criterion": defect.criterion,
        "blocking": defect.blocking,
        "chapter": defect.chapter,
        "message": defect.message,
    }


@dataclass(frozen=True)
class Gate:
    production: Production
    lean: LeanStage
    visual_review: VisualReview
    pdf: PdfStage
    judge_prompt: str
    judge_prompt_version: str | None = None

    async def __call__(self, run_id: int, trace: Trace) -> None:
        while True:
            job = self._start_pass(run_id)
            result = await self._pass(job, trace)
            verdict = result.verdict
            if verdict.outcome == "interrupted":
                raise RunStop("interrupted", cast(str, verdict.reason), result.detail)
            if verdict.outcome == "continue":
                self._publish(job, cast(str, result.pdf_path))
                return
            with unit_of_work(self.production.session_factory) as uow:
                record_pass(uow, run_id, job.cycle, verdict.outcome)
                if verdict.outcome == "rewrite":
                    run = get_run(uow.session, run_id)
                    run.phase, run.chapter = "rewriting", None
            if verdict.outcome == "fail":
                raise RunStop("failed", cast(str, verdict.reason), result.detail)
            if result.reregister:
                await self._reregister(job, verdict.chapters_to_rewrite, result.defects, trace)
            else:
                await self._rewrite(job, verdict.chapters_to_rewrite, result.defects, trace)

    # --- Arranque de una pasada -----------------------------------------------------------------

    def _start_pass(self, run_id: int) -> GateJob:
        """Fase `gate` y la pasada siguiente a las ya contadas. Solo corre sobre una candidata con
        sus 10 capítulos (012-C1)."""
        p = self.production
        with unit_of_work(p.session_factory) as uow:
            session = uow.session
            run = get_run(session, run_id)
            run.phase, run.chapter = "gate", None
            version_id = run.candidate_version_id
            novel = session.get(Novel, run.novel_id)
            if version_id is None or novel is None:
                raise LookupError(f"la ejecución {run_id} no tiene novela o candidata")
            chapters = session.query(Chapter).filter(Chapter.version_id == version_id).count()
            if chapters != CHAPTERS_PER_NOVEL:
                raise RuntimeError(
                    f"el gate solo corre con {CHAPTERS_PER_NOVEL} capítulos aceptados; "
                    f"la candidata tiene {chapters}"
                )
            counted = (
                session.query(Attempt)
                .filter(
                    Attempt.run_id == run_id,
                    Attempt.evaluable == GATE_EVALUABLE,
                    Attempt.outcome.is_not(None),
                )
                .count()
            )
            cycle = counted + 1
            return GateJob(
                run_id=run_id,
                user_id=novel.user_id,
                novel_id=novel.id,
                version_id=version_id,
                cycle=cycle,
                cycles_remaining=cycle < 1 + p.config.max_retries["gate_cycles"],
            )

    # --- Una pasada: cuatro etapas en orden, cortando en la que no pasa (012-C7) --------------

    async def _pass(self, job: GateJob, trace: Trace) -> PassResult:
        for stage in (self._stage_1, self._stage_2, self._stage_3):
            result = await stage(job, trace)
            if result.verdict.outcome != "continue":
                return result
        return await self._stage_4(job, trace)

    async def _stage_1(self, job: GateJob, trace: Trace) -> PassResult:
        """Deterministas: `elementos-obligatorios`, `nombres-exactos` y `palabras-prohibidas`
        sobre los capítulos; corren los tres aunque falle el primero."""
        with self.production.session_factory() as session:
            chapters = inputs.chapters_of(session, job.version_id)
            elements, used = inputs.mandatory_elements(session, job.version_id)
            names = inputs.canonical_names(session, job.version_id)
            texts = inputs.chapter_texts(chapters)
            matches = inputs.banned_matches(session, job.user_id, job.novel_id, texts)
        mandatory = mandatory_elements_result(elements, used)
        exact = inputs.exact_names_result(chapters, names)
        banned, decision = banned_terms_in_chapters(texts, matches)
        self._record_decision(job, decision)
        self._record(job, trace, mandatory.validator, mandatory.passed, mandatory.defects)
        self._record(job, trace, exact.validator, exact.passed, exact.defects)
        self._record(
            job, trace, BANNED_TERMS_VALIDATOR, banned.passed, banned.defects, _banned(banned)
        )
        defects = (*mandatory.defects, *exact.defects, *banned.defects)
        verdict = gate_precedence(defects=defects, cycles_remaining=job.cycles_remaining)
        return PassResult(verdict, defects, _messages(defects))

    async def _stage_2(self, job: GateJob, trace: Trace) -> PassResult:
        """`cronologia-lean` ∥ `juez-novela`: se espera a los dos y se combinan sus defectos."""
        telemetry = self.production.telemetry
        with telemetry.span(trace, f"validador:{JUDGE}") as judge_span:
            verification, judge = await asyncio.gather(
                self.lean(job.run_id), self._judge(job, trace, judge_span)
            )
            judged = self._judge_outcome(job, trace, judge_span, judge)
        lean = self._lean_outcome(job, trace, verification)
        defects = (*lean.defects, *judged.defects)
        verdict = gate_precedence(
            unattributable_reason=lean.unattributable,
            interruption_reason=lean.interruption or judged.interruption,
            defects=defects,
            judge_no_valid_delivery=judged.no_valid_delivery,
            cycles_remaining=job.cycles_remaining,
        )
        if verdict.outcome in ("fail", "interrupted") and verdict.reason != "retries_exhausted":
            detail = "; ".join(x for x in (lean.detail, judged.detail) if x)
        else:
            detail = _messages([d for d in defects if d.blocking]) + (
                f"; {judged.detail}" if judged.detail else ""
            )
        return PassResult(verdict, defects, detail)

    def _lean_outcome(
        self, job: GateJob, trace: Trace, verification: CandidateVerification
    ) -> _StageTwoPart:
        outcome = verification.outcome
        if isinstance(outcome, VerifierInterruption):
            return _StageTwoPart(
                interruption=outcome.reason,
                detail=f"verificador: {outcome.detail or outcome.reason}",
            )
        with self.production.session_factory() as session:
            bible = read_story_bible(session, job.version_id)
        lean = lean_stage_result(outcome, bible)
        comment = f"no compila: {lean.internal_error}" if lean.internal_error else None
        self._record(job, trace, LEAN, lean.passed, lean.defects, comment, _holds(outcome))
        if lean.internal_error is not None:
            return _StageTwoPart(
                unattributable="internal_error",
                detail=f"el FicheroDeCronologia no compila: {lean.internal_error}",
            )
        if lean.unattributable:
            witness = [d for d in lean.defects if d.chapter is None]
            return _StageTwoPart(
                lean.defects, unattributable="unattributable_defect", detail=_messages(witness)
            )
        return _StageTwoPart(lean.defects)

    def _judge_outcome(
        self, job: GateJob, trace: Trace, span: Span, judge: JudgeRun
    ) -> _StageTwoPart:
        if judge.provider_error:
            return _StageTwoPart(
                interruption="provider_error",
                detail="la sesión del juez terminó por un error del proveedor",
            )
        if judge.evaluation is None:
            self._record(job, trace, JUDGE, False, (), "sin evaluación válida", span=span)
            return _StageTwoPart(
                no_valid_delivery=True, detail="el juez terminó sin una evaluación válida"
            )
        evaluation = judge.evaluation
        verdict = judge_result(evaluation, self.production.config.thresholds)
        parts = tuple(
            (c.name, evaluation.get(c.name).score, evaluation.get(c.name).justification)
            for c in NOVEL_RUBRIC
        )
        self._record(job, trace, JUDGE, verdict.passed, verdict.defects, parts=parts, span=span)
        return _StageTwoPart(verdict.defects)

    async def _stage_3(self, job: GateJob, trace: Trace) -> PassResult:
        review = await self.visual_review(job, trace)
        verdict = gate_precedence(
            unattributable_reason=review.failure,
            interruption_reason=review.interruption,
            defects=review.defects,
            # Como el juez sin evaluación válida (012-C15): un ciclo fallido sin capítulos.
            judge_no_valid_delivery=review.no_valid_delivery,
            cycles_remaining=job.cycles_remaining,
        )
        detail = review.detail or _messages(review.defects)
        return PassResult(verdict, review.defects, detail, reregister=review.reregister)

    async def _stage_4(self, job: GateJob, trace: Trace) -> PassResult:
        """El PDF de la candidata: sin PDF o con un enlace interno roto, `render_failure`, sin
        reescritura (012-C18)."""
        pdf = await self.pdf(job.version_id)
        if pdf.path is None:
            return PassResult(PassVerdict("fail", "render_failure"), detail=pdf.detail or "sin PDF")
        self._record(job, trace, PDF_LINKS, pdf.links_passed, (), pdf.detail or None)
        if not pdf.links_passed:
            return PassResult(PassVerdict("fail", "render_failure"), detail=pdf.detail)
        return PassResult(PassVerdict("continue"), pdf_path=pdf.path)

    # --- Juez --------------------------------------------------------------------------------

    async def _judge(self, job: GateJob, trace: Trace, span: Span) -> JudgeRun:
        """Una sesión del juez con su única tool; la primera entrega válida es la evaluación. Las
        inválidas vuelven al juez como error de schema en la misma sesión (003, 012-C15)."""
        with self.production.session_factory() as session:
            message = inputs.judge_message(session, job.version_id, job.novel_id)
        request = SessionRequest(
            role="judge",
            mode=None,
            user_id=job.user_id,
            novel_id=job.novel_id,
            prompt=self.judge_prompt,
            prompt_version=self.judge_prompt_version,
            message=message,
            tools=(submit_evaluation_tool(),),
            trace=trace,
            parent_span=span,
            run_id=job.run_id,
        )
        result = await self.production.port.run(request)
        if result.outcome == "infrastructure_failure":
            return JudgeRun(None, provider_error=True)
        deliveries = result.deliveries
        evaluation = cast(JudgeEvaluation, deliveries[0].value) if deliveries else None
        return JudgeRun(evaluation, provider_error=False)

    # --- Resultados y scores (012-C24) --------------------------------------------------------

    def _record(
        self,
        job: GateJob,
        trace: Trace,
        validator: str,
        passed: bool,
        defects: Sequence[Defect],
        comment: str | None = None,
        parts: Sequence[tuple[str, int, str | None]] = (),
        span: Span | None = None,
    ) -> None:
        """Primero el `ResultadoDeValidador`; una vez guardado, su score (y los de sus partes)
        dentro del span `validador:<nombre>` (el de la sesión del juez, si ya está abierto)."""
        comment = comment or _messages(defects)
        detail: dict[str, Any] = {
            "gate_cycle": job.cycle,
            "comment": comment,
            "defects": [_defect_detail(d) for d in defects],
        }
        if parts:
            detail["parts"] = [{"name": n, "score": s, "comment": c} for n, s, c in parts]
        p = self.production
        with unit_of_work(p.session_factory) as uow:
            uow.add(
                ValidatorResult(
                    run_id=job.run_id,
                    version_id=job.version_id,
                    validator=validator,
                    chapter=None,
                    passed=passed,
                    score=1.0 if passed else 0.0,
                    detail=detail,
                    created_at=naive(p.clock()),
                )
            )
        if span is not None:
            self._scores(trace, validator, passed, comment, parts, span)
            return
        with p.telemetry.span(trace, f"validador:{validator}") as own:
            self._scores(trace, validator, passed, comment, parts, own)

    def _scores(
        self,
        trace: Trace,
        validator: str,
        passed: bool,
        comment: str,
        parts: Sequence[tuple[str, int, str | None]],
        span: Span,
    ) -> None:
        telemetry = self.production.telemetry
        telemetry.score(trace, validator, 1 if passed else 0, comment, span)
        for name, score, part_comment in parts:
            telemetry.score(trace, f"{validator}/{name}", score, part_comment, span)

    def _record_decision(self, job: GateJob, decision: DecisionDePolitica) -> None:
        """Una decisión de política por pasada, con origen `publication_gate` (012-C5)."""
        request = PeticionDePolitica(
            origen="publication_gate",
            cliente=str(job.user_id),
            novela=str(job.novel_id),
            ejecucion=str(job.run_id),
        )
        with unit_of_work(self.production.session_factory) as uow:
            record_decision(uow, request, decision)

    # --- Reescritura dirigida y publicación ----------------------------------------------------

    async def _rewrite(
        self, job: GateJob, chapters: Sequence[int], defects: Sequence[Defect], trace: Trace
    ) -> None:
        producer = ChapterProducer(self.production)
        for chapter in sorted(chapters):
            with unit_of_work(self.production.session_factory) as uow:
                run = get_run(uow.session, job.run_id)
                run.phase, run.chapter = "rewriting", chapter
            own = [d for d in defects if d.chapter == chapter]
            await producer.produce_chapter(
                job.run_id,
                chapter,
                trace,
                gate_cycle=job.cycle,
                defects=tuple(_entry(d) for d in own),
                editor_defects=tuple(_entry(d) for d in own if d.validator == LEAN),
            )

    async def _reregister(
        self, job: GateJob, chapters: Sequence[int], defects: Sequence[Defect], trace: Trace
    ) -> None:
        """Un fallo de datos de `revision-visual`: el editor vuelve a registrar cada capítulo
        atribuido, sin writer (§9.4; 017-C17)."""
        for chapter in sorted(chapters):
            with unit_of_work(self.production.session_factory) as uow:
                run = get_run(uow.session, job.run_id)
                run.phase, run.chapter = "rewriting", chapter
            await reregister_chapter(
                self.production,
                run_id=job.run_id,
                user_id=job.user_id,
                novel_id=job.novel_id,
                version_id=job.version_id,
                gate_cycle=job.cycle,
                chapter=chapter,
                defects=tuple(_entry(d) for d in defects if d.chapter == chapter),
                trace=trace,
            )

    def _publish(self, job: GateJob, pdf_path: str) -> None:
        """Si la transacción falla, no queda nada escrito y la ejecución cae con `crash`: al
        reanudar, se repasa el gate (012-C23 d)."""
        p = self.production
        try:
            with unit_of_work(p.session_factory) as uow:
                publish_candidate(
                    uow, run_id=job.run_id, cycle=job.cycle, pdf_path=pdf_path, now=p.clock()
                )
        except Exception as exc:
            raise RunStop(
                "interrupted", "crash", f"falló la transacción de publicación: {exc}"
            ) from exc


def _entry(defect: Defect) -> dict[str, Any]:
    return defect_entry(defect.validator, defect.message, defect.blocking, defect.criterion)


def _holds(result: ChronologyResult) -> tuple[tuple[str, int, str | None], ...]:
    if result.result == "error":
        return ()
    return tuple((t, 1 if result.holds.get(t, False) else 0, None) for t in INVARIANTS)


def _banned(result: NovelValidatorResult) -> str:
    """El comentario de `palabras-prohibidas`: término, nivel y variante de cada coincidencia."""
    return _messages(result.defects) if result.defects else "sin coincidencias"

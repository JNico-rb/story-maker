"""Producción de capítulos: por cada capítulo, ventana → writer con sus hooks → editor → veredicto
por código → transacción de aceptación (`architecture.md` §8; spec 011).

Qué cuenta como intento (011-C13 a 011-C15): cada `submit_chapter` rechazado por la policy, el
schema o el hook de validación; una sesión del writer sin entrega válida; una del editor sin
revisión válida; y cada revisión juzgada. No cuentan las denegaciones de otras tools, los errores
de schema del editor ni un error del proveedor, que interrumpe la ejecución (§7.6)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal, cast

from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.port import AgentPort, Defect, SessionRequest, SessionResult, ToolCall
from story_maker.config import Config
from story_maker.domain.constants import CHAPTERS_PER_NOVEL
from story_maker.observability.port import ObservabilityPort, Span, Trace
from story_maker.pipeline.acceptance import (
    CHAPTER_EVALUABLE,
    CardSync,
    ValidatorRun,
    accept_chapter,
    record_closed_attempt,
)
from story_maker.pipeline.runs import Clock, RunStop, get_run
from story_maker.pipeline.submissions import (
    SUBMIT_CHAPTER,
    ChapterSubmission,
    Citable,
    citable,
    submit_chapter_tool,
    submit_review_tool,
)
from story_maker.pipeline.windows import (
    WindowBuilder,
    WriterWindow,
    editor_message,
    writer_message,
)
from story_maker.store.models import Attempt, Character, Novel
from story_maker.store.session import unit_of_work
from story_maker.validators.chapter_check import ChapterCheck
from story_maker.validators.chapter_length import check_chapter_length, count_words
from story_maker.validators.chapter_rubric import (
    RUBRIC,
    ChapterReview,
    RubricJudgement,
    judge_review,
)
from story_maker.validators.exact_names import check_exact_names

Verdict = Literal["accept", "rewrite", "fail"]
BANNED_RULE = "palabras-prohibidas"


@dataclass(frozen=True)
class Prompts:
    """El prompt versionado del writer (modos `write` y `rewrite`) y el del editor (§13.4)."""

    writer: str
    editor: str
    writer_version: str | None = None
    editor_version: str | None = None


@dataclass(frozen=True)
class Production:
    port: AgentPort
    session_factory: sessionmaker[Session]
    telemetry: ObservabilityPort
    config: Config
    windows: WindowBuilder
    cards: CardSync
    clock: Clock
    prompts: Prompts

    @property
    def max_attempts(self) -> int:
        return 1 + self.config.max_retries["chapter"]


@dataclass(frozen=True)
class ChapterJob:
    run_id: int
    user_id: int
    novel_id: int
    version_id: int
    chapter: int
    canonical_names: tuple[str, ...]
    citable: Citable


@dataclass(frozen=True)
class Delivery:
    """La primera entrega que pasó los hooks: el intento que juzga el editor."""

    number: int
    submission: ChapterSubmission
    runs: tuple[ValidatorRun, ...]


@dataclass(frozen=True)
class ClosedAttempt:
    number: int
    outcome: Verdict
    runs: tuple[ValidatorRun, ...]
    defects: tuple[dict[str, Any], ...]
    banned: bool = False


@dataclass(frozen=True)
class WriterOutcome:
    closed: tuple[ClosedAttempt, ...]
    delivery: Delivery | None
    provider_error: bool


def defect_entry(
    validator: str, message: str, blocking: bool, criterion: str | None = None
) -> dict[str, Any]:
    return {
        "validator": validator,
        "criterion": criterion,
        "blocking": blocking,
        "message": message,
    }


def verdict(passed: bool, attempt: int, max_attempts: int) -> Verdict:
    """`accept` sin bloqueantes; si los hay, `rewrite` mientras queden intentos y `fail` al
    agotarlos (`definitions.md` §6 Veredicto)."""
    if passed:
        return "accept"
    return "rewrite" if attempt < max_attempts else "fail"


def check_run(check: ChapterCheck) -> ValidatorRun:
    return ValidatorRun(
        validator=check.validator,
        passed=check.passed,
        comment=check.comment,
        defects=tuple(defect_entry(d.validator, d.message, d.blocking) for d in check.defects),
    )


def rubric_run(judgement: RubricJudgement) -> ValidatorRun:
    return ValidatorRun(
        validator=RUBRIC,
        passed=judgement.passed,
        comment="; ".join(d.message for d in judgement.blocking) or "sin defectos bloqueantes",
        defects=tuple(
            defect_entry(RUBRIC, d.message, d.blocking, d.criterion) for d in judgement.defects
        ),
        parts=tuple((s.criterion, s.score, s.justification) for s in judgement.scores),
    )


class _ChapterHooks:
    """El hook de validación de capítulo: `longitud-capitulo` y `nombres-exactos` sobre cada
    entrega que la policy y el schema dejaron pasar, en orden (§7.5)."""

    def __init__(self, canonical_names: Sequence[str]) -> None:
        self._names = tuple(canonical_names)
        self.log: list[tuple[ChapterCheck, ...]] = []

    def __call__(self, value: BaseModel) -> list[Defect]:
        submission = cast(ChapterSubmission, value)  # la tool solo valida contra este modelo
        checks = (
            check_chapter_length(submission.text),
            check_exact_names(submission.title, submission.text, self._names),
        )
        self.log.append(checks)
        return [defect for check in checks for defect in check.defects]


class _AttemptLimit:
    """Corta la sesión del writer cuando sus entregas rechazadas agotan los intentos (011-C18)."""

    def __init__(self, used: int, max_attempts: int) -> None:
        self._used = used
        self._max = max_attempts
        self._rejected = 0
        self._delivered = False

    def __call__(self, call: ToolCall) -> bool:
        if call.tool != SUBMIT_CHAPTER or self._delivered:
            return False
        if call.status == "accepted":
            self._delivered = True
            return False
        self._rejected += 1
        return self._used + self._rejected >= self._max


def _rejection(call: ToolCall) -> tuple[tuple[dict[str, Any], ...], bool]:
    """Los defectos que recibe el writer de una entrega rechazada y si la causa fue una
    prohibida."""
    if call.status == "denied":
        reason = call.reason or ""
        banned = reason.startswith(BANNED_RULE)
        return (defect_entry(BANNED_RULE if banned else "politica", reason, True),), banned
    if call.status == "schema_rejected":
        return (defect_entry("schema-salida", "; ".join(call.errors), True),), False
    return tuple(defect_entry(d.validator, d.message, d.blocking) for d in call.defects), False


def interpret_writer(
    result: SessionResult,
    hooks_log: Sequence[tuple[ChapterCheck, ...]],
    used: int,
    max_attempts: int,
) -> WriterOutcome:
    """Los intentos que cerró la sesión del writer y la entrega que pasa al editor, si la hay."""
    checks = iter(hooks_log)
    number = used
    closed: list[ClosedAttempt] = []
    delivery: Delivery | None = None
    for call in result.calls:
        if call.tool != SUBMIT_CHAPTER or number >= max_attempts:
            continue
        runs = (
            tuple(check_run(c) for c in next(checks))
            if call.status in ("accepted", "blocked")
            else ()
        )
        if call.status == "accepted":
            delivery = Delivery(number + 1, cast(ChapterSubmission, call.value), runs)
            break
        number += 1
        defects, banned = _rejection(call)
        closed.append(
            ClosedAttempt(number, verdict(False, number, max_attempts), runs, defects, banned)
        )
    provider_error = result.outcome == "infrastructure_failure"
    if delivery is None and not provider_error and number < max_attempts:
        # La sesión terminó sin entrega válida: el intento en curso es fallido (011-C14).
        number += 1
        closed.append(ClosedAttempt(number, verdict(False, number, max_attempts), (), ()))
    return WriterOutcome(tuple(closed), delivery, provider_error)


class ChapterProducer:
    def __init__(self, production: Production) -> None:
        self.p = production

    def _now(self) -> dt.datetime:
        return self.p.clock()

    async def produce(self, run_id: int, trace: Trace, first: int) -> None:
        """Del capítulo `first` al 10, en secuencia."""
        for chapter in range(first, CHAPTERS_PER_NOVEL + 1):
            with unit_of_work(self.p.session_factory) as uow:
                run = get_run(uow.session, run_id)
                run.phase, run.chapter = "writing", chapter
            await self.produce_chapter(run_id, chapter, trace)

    def _job(self, run_id: int, chapter: int) -> ChapterJob:
        with self.p.session_factory() as session:
            run = get_run(session, run_id)
            novel = session.get(Novel, run.novel_id)
            version_id = run.candidate_version_id
            if novel is None or version_id is None:
                raise LookupError(f"la ejecución {run_id} no tiene novela o candidata")
            names = session.query(Character.canonical_name).filter(
                Character.version_id == version_id
            )
            return ChapterJob(
                run_id=run_id,
                user_id=novel.user_id,
                novel_id=novel.id,
                version_id=version_id,
                chapter=chapter,
                canonical_names=tuple(row[0] for row in names.order_by(Character.id)),
                citable=citable(session, version_id, chapter),
            )

    def _closed_attempts(self, run_id: int, chapter: int) -> int:
        """Los intentos que ya cuentan: los intentos no se reinician al reanudar y el que cortó
        una caída, sin desenlace, no cuenta (§7.6)."""
        with self.p.session_factory() as session:
            return (
                session.query(Attempt)
                .filter(
                    Attempt.run_id == run_id,
                    Attempt.evaluable == CHAPTER_EVALUABLE,
                    Attempt.chapter == chapter,
                    Attempt.gate_cycle.is_(None),
                    Attempt.outcome.is_not(None),
                )
                .count()
            )

    async def produce_chapter(self, run_id: int, chapter: int, trace: Trace) -> None:
        with self.p.telemetry.span(trace, f"capitulo-{chapter}") as span:
            job = self._job(run_id, chapter)
            with self.p.session_factory() as session:
                window = self.p.windows.writer(session, job.version_id, chapter)
            used = self._closed_attempts(run_id, chapter)
            mode, defects = "write", tuple[dict[str, Any], ...]()
            while True:
                written = await self._write(job, window, mode, defects, used, trace, span)
                self._close(job, written.closed, trace, span)
                used += len(written.closed)
                if written.provider_error:
                    raise RunStop("interrupted", "provider_error", self._where(job, "writer"))
                if written.delivery is None:
                    last = written.closed[-1]
                    if last.outcome == "fail":
                        reason = "banned_content" if last.banned else "retries_exhausted"
                        raise RunStop("failed", reason, self._exhausted(job, last))
                    mode = "rewrite"
                    defects = next((a.defects for a in reversed(written.closed) if a.defects), ())
                    continue
                delivery = written.delivery
                review = await self._review(job, delivery, trace, span)
                if review is None:
                    closed = ClosedAttempt(
                        delivery.number,
                        verdict(False, delivery.number, self.p.max_attempts),
                        delivery.runs,
                        (),
                    )
                else:
                    judgement = judge_review(review, self.p.config.thresholds)
                    runs = (*delivery.runs, rubric_run(judgement))
                    outcome = verdict(judgement.passed, delivery.number, self.p.max_attempts)
                    if outcome == "accept":
                        self._accept(job, delivery, review, runs)
                        self._emit(trace, span, runs)
                        return
                    closed = ClosedAttempt(delivery.number, outcome, runs, runs[-1].defects)
                self._close(job, (closed,), trace, span)
                used += 1
                if closed.outcome == "fail":
                    raise RunStop("failed", "retries_exhausted", self._exhausted(job, closed))
                mode, defects = "rewrite", closed.defects

    def _request(self, job: ChapterJob, trace: Trace, span: Span, **fields: Any) -> SessionRequest:
        return SessionRequest(
            user_id=job.user_id,
            novel_id=job.novel_id,
            trace=trace,
            parent_span=span,
            run_id=job.run_id,
            chapter=job.chapter,
            **fields,
        )

    async def _write(
        self,
        job: ChapterJob,
        window: WriterWindow,
        mode: str,
        defects: Sequence[dict[str, Any]],
        used: int,
        trace: Trace,
        span: Span,
    ) -> WriterOutcome:
        hooks = _ChapterHooks(job.canonical_names)
        request = self._request(
            job,
            trace,
            span,
            role="writer",
            mode=mode,
            prompt=self.p.prompts.writer,
            prompt_version=self.p.prompts.writer_version,
            message=writer_message(window, defects),
            tools=(submit_chapter_tool(),),
            chapter_checks=hooks,
            cut_when=_AttemptLimit(used, self.p.max_attempts),
        )
        result = await self.p.port.run(request)
        return interpret_writer(result, hooks.log, used, self.p.max_attempts)

    async def _review(
        self, job: ChapterJob, delivery: Delivery, trace: Trace, span: Span
    ) -> ChapterReview | None:
        """La primera revisión válida del editor, o ninguna si su sesión termina sin ella."""
        title, text = delivery.submission.title, delivery.submission.text
        with self.p.session_factory() as session:
            window = self.p.windows.editor(session, job.version_id, job.chapter, title, text)
        request = self._request(
            job,
            trace,
            span,
            role="editor",
            mode=None,
            prompt=self.p.prompts.editor,
            prompt_version=self.p.prompts.editor_version,
            message=editor_message(window, title, text, lint_defects=()),
            tools=(submit_review_tool(job.citable),),
        )
        result = await self.p.port.run(request)
        if result.outcome == "infrastructure_failure":
            raise RunStop("interrupted", "provider_error", self._where(job, "editor"))
        deliveries = result.deliveries
        return cast(ChapterReview, deliveries[0].value) if deliveries else None

    def _close(
        self, job: ChapterJob, closed: Sequence[ClosedAttempt], trace: Trace, span: Span
    ) -> None:
        """Los intentos cerrados sin aceptar quedan con su desenlace y sus resultados; sus scores
        salen al cerrarse."""
        if not closed:
            return
        with unit_of_work(self.p.session_factory) as uow:
            for attempt in closed:
                record_closed_attempt(
                    uow,
                    run_id=job.run_id,
                    version_id=job.version_id,
                    chapter=job.chapter,
                    number=attempt.number,
                    outcome=attempt.outcome,
                    runs=attempt.runs,
                    now=self._now(),
                )
        for attempt in closed:
            self._emit(trace, span, attempt.runs)

    def _accept(
        self,
        job: ChapterJob,
        delivery: Delivery,
        review: ChapterReview,
        runs: Sequence[ValidatorRun],
    ) -> None:
        """Si la transacción falla, no queda nada del capítulo y la ejecución cae con `crash`:
        al reanudar, el capítulo se rehace (§8.3; 011-C21)."""
        submission = delivery.submission
        try:
            with unit_of_work(self.p.session_factory) as uow:
                accept_chapter(
                    uow,
                    run_id=job.run_id,
                    version_id=job.version_id,
                    chapter=job.chapter,
                    title=submission.title,
                    text=submission.text,
                    word_count=count_words(submission.text),
                    review=review,
                    attempt=delivery.number,
                    runs=runs,
                    cards=self.p.cards,
                    now=self._now(),
                )
        except Exception as exc:
            raise RunStop(
                "interrupted",
                "crash",
                f"capítulo {job.chapter}: falló la transacción de aceptación: {exc}",
            ) from exc

    def _emit(self, trace: Trace, span: Span, runs: Sequence[ValidatorRun]) -> None:
        for run in runs:
            self.p.telemetry.score(trace, run.validator, 1 if run.passed else 0, run.comment, span)
            for criterion, score, justification in run.parts:
                self.p.telemetry.score(
                    trace, f"{run.validator}/{criterion}", score, justification, span
                )

    def _where(self, job: ChapterJob, role: str) -> str:
        return f"capítulo {job.chapter}: la sesión del {role} terminó por un error del proveedor"

    def _exhausted(self, job: ChapterJob, last: ClosedAttempt) -> str:
        messages = "; ".join(d["message"] for d in last.defects) or "sin entrega válida"
        return (
            f"capítulo {job.chapter}: {self.p.max_attempts} intentos agotados; último: {messages}"
        )

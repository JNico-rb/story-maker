"""Aceptar un capítulo: una sola transacción con todo lo que deja en la candidata, y el registro de
los intentos que se cierran sin aceptar (`architecture.md` §8.3, §9.2; 011-C19 a 011-C22).

Las CanonCards sucesoras las decide y escribe 016 (texto, huella, índice, qué entidades cambian)
dentro de esta misma transacción: aquí llegan por la costura `CardSync`."""

from __future__ import annotations

import datetime as dt
import hashlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from story_maker.domain.banned_terms import find_term_matches
from story_maker.domain.constants import CHAPTERS_PER_NOVEL
from story_maker.pipeline.runs import get_run, naive
from story_maker.store.brief_canon import NOMINAL_ATTRIBUTES
from story_maker.store.models import (
    Attempt,
    Chapter,
    Checkpoint,
    Event,
    EventCharacter,
    Fact,
    FactUsage,
    ValidatorResult,
)
from story_maker.store.session import UnitOfWork
from story_maker.validators.chapter_rubric import ChapterReview

CHAPTER_EVALUABLE = "chapter"

# Sincroniza las CanonCards de la versión con su story bible, sin confirmar (016).
CardSync = Callable[[UnitOfWork, int], None]


@dataclass(frozen=True)
class ValidatorRun:
    """Una vez que corre un validador sobre un intento: su `ResultadoDeValidador` y sus scores
    (0/1 y, en una rúbrica, uno de 1 a 5 por criterio)."""

    validator: str
    passed: bool
    comment: str
    defects: tuple[dict[str, Any], ...] = ()
    parts: tuple[tuple[str, int, str], ...] = field(default=())

    def detail(self, attempt: int) -> dict[str, Any]:
        detail: dict[str, Any] = {
            "attempt": attempt,
            "comment": self.comment,
            "defects": [dict(d) for d in self.defects],
        }
        if self.parts:
            detail["criteria"] = [
                {"criterion": c, "score": s, "justification": j} for c, s, j in self.parts
            ]
        return detail


def chapter_hash(title: str, text: str) -> str:
    """Huella del título y el texto (`definitions.md` §3 Capitulo)."""
    return hashlib.sha256(f"{title}\n{text}".encode()).hexdigest()


def literal_usages(session: Session, version_id: int, text: str) -> set[int]:
    """Los hechos nominales de la versión cuyo valor aparece en el texto, por tokens en la forma
    normalizada de 005: respeta los límites de palabra (011-C20)."""
    facts = session.query(Fact).filter(
        Fact.version_id == version_id, Fact.attribute.in_(NOMINAL_ATTRIBUTES)
    )
    return {fact.id for fact in facts if find_term_matches(text, fact.value)}


def record_validator_results(
    uow: UnitOfWork,
    *,
    run_id: int,
    version_id: int,
    chapter: int,
    attempt: int,
    runs: Sequence[ValidatorRun],
    now: dt.datetime,
) -> None:
    for run in runs:
        uow.add(
            ValidatorResult(
                run_id=run_id,
                version_id=version_id,
                validator=run.validator,
                chapter=chapter,
                passed=run.passed,
                score=1.0 if run.passed else 0.0,
                detail=run.detail(attempt),
                created_at=naive(now),
            )
        )


def record_closed_attempt(
    uow: UnitOfWork,
    *,
    run_id: int,
    version_id: int,
    chapter: int,
    number: int,
    outcome: str,
    runs: Sequence[ValidatorRun],
    now: dt.datetime,
    gate_cycle: int | None = None,
) -> None:
    """Un intento del capítulo cerrado sin aceptar (`rewrite` o `fail`) y lo que corrió en él; en
    la reescritura dirigida, dentro de su ciclo del gate (012-C20)."""
    uow.add(
        Attempt(
            run_id=run_id,
            evaluable=CHAPTER_EVALUABLE,
            chapter=chapter,
            gate_cycle=gate_cycle,
            number=number,
            outcome=outcome,
        )
    )
    record_validator_results(
        uow,
        run_id=run_id,
        version_id=version_id,
        chapter=chapter,
        attempt=number,
        runs=runs,
        now=now,
    )


def _remove_previous_acceptance(uow: UnitOfWork, version_id: int, chapter: int) -> None:
    """Lo que dejó una aceptación anterior del capítulo en esta candidata: su fila, sus usos y sus
    eventos registrados (011-C22)."""
    session = uow.session
    for row in session.query(Chapter).filter(
        Chapter.version_id == version_id, Chapter.number == chapter
    ):
        uow.delete(row)
    usages = (
        session.query(FactUsage)
        .join(Fact, Fact.id == FactUsage.fact_id)
        .filter(Fact.version_id == version_id, FactUsage.chapter == chapter)
    )
    for usage in usages:
        uow.delete(usage)
    events = (
        session.query(Event)
        .filter(
            Event.version_id == version_id, Event.origin == "recorded", Event.chapter == chapter
        )
        .all()
    )
    for event in events:
        for presence in session.query(EventCharacter).filter(EventCharacter.event_id == event.id):
            uow.delete(presence)
    session.flush()  # sin relaciones mapeadas, las presencias se borran antes que su evento
    for event in events:
        uow.delete(event)
    session.flush()


def _record_events(uow: UnitOfWork, version_id: int, chapter: int, review: ChapterReview) -> None:
    for narrated in review.events:
        event = Event(
            version_id=version_id,
            statement=narrated.statement,
            moment=naive(narrated.moment),
            place_id=narrated.place_id,
            type=narrated.type,
            excluded_character_id=narrated.excluded_character_id,
            analepsis=narrated.analepsis,
            origin="recorded",
            chapter=chapter,
            beat=narrated.beat,
        )
        uow.add(event)
        uow.session.flush()
        for presence in narrated.present:
            uow.add(
                EventCharacter(
                    event_id=event.id, character_id=presence.character_id, declared_age=presence.age
                )
            )


def accept_chapter(
    uow: UnitOfWork,
    *,
    run_id: int,
    version_id: int,
    chapter: int,
    title: str,
    text: str,
    word_count: int,
    review: ChapterReview,
    attempt: int,
    runs: Sequence[ValidatorRun],
    cards: CardSync,
    now: dt.datetime,
    gate_cycle: int | None = None,
) -> None:
    """Todo o nada en la transacción de `uow`. En fase `writing` escribe además el
    `PuntoDeControl` del capítulo y avanza la ejecución; en `gate` o `rewriting` no (§8.3)."""
    session = uow.session
    run = get_run(session, run_id)
    _remove_previous_acceptance(uow, version_id, chapter)
    uow.add(
        Chapter(
            version_id=version_id,
            number=chapter,
            title=title,
            text=text,
            summary=review.summary,
            word_count=word_count,
            content_hash=chapter_hash(title, text),
        )
    )
    for fact_id in sorted(set(review.fact_usages) | literal_usages(session, version_id, text)):
        uow.add(FactUsage(fact_id=fact_id, chapter=chapter))
    _record_events(uow, version_id, chapter, review)
    session.flush()
    cards(uow, version_id)
    record_validator_results(
        uow,
        run_id=run_id,
        version_id=version_id,
        chapter=chapter,
        attempt=attempt,
        runs=runs,
        now=now,
    )
    uow.add(
        Attempt(
            run_id=run_id,
            evaluable=CHAPTER_EVALUABLE,
            chapter=chapter,
            gate_cycle=gate_cycle,
            number=attempt,
            outcome="accept",
        )
    )
    if run.phase == "writing":
        if chapter == CHAPTERS_PER_NOVEL:
            run.phase, run.chapter = "gate", None
        else:
            run.chapter = chapter + 1
        session.flush()
        uow.add(Checkpoint(run_id=run_id, chapter=chapter, created_at=naive(now)))
    session.flush()

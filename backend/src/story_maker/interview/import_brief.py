"""Brief importado en JSON: las mismas comprobaciones que confirmar, antes de extraer nada; si
pasan, cada texto libre pasa por el mismo extractor y el brief queda confirmado
(`architecture.md` §3.4; 008-C28 a 008-C30)."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

from pydantic import Field, ValidationError
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.port import AgentPort, PolicyEngine
from story_maker.domain.brief import BannedEntry, BriefContent, brief_problems
from story_maker.interview.banned_terms import add_banned_term
from story_maker.interview.brief import BannedEntryPatch
from story_maker.interview.free_text import (
    MAX_FREE_TEXT_CHARS,
    FreeTextFailure,
    import_trace_key,
    run_free_text,
)
from story_maker.interview.novels import load_banned_entries
from story_maker.observability.port import ObservabilityPort
from story_maker.store.models import Brief, ExtractedFact, Interview, Novel
from story_maker.store.session import unit_of_work

TRACE_NAME = "importacion"


class BriefImportIn(BriefContent):
    """B0 en JSON, más las entradas prohibidas de nivel `novel` y los textos libres a extraer
    (008-C28). `extra="forbid"` hereda de `BriefContent`: un campo que el brief no tiene se
    rechaza igual que cualquier otro error de forma (008-C29)."""

    banned_entries: list[BannedEntryPatch] = Field(default_factory=list)
    free_texts: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class ImportResult:
    novel_id: int


@dataclass(frozen=True)
class ImportRejected:
    problems: list[dict[str, Any]]


@dataclass(frozen=True)
class ImportFailure:
    novel_id: int
    reason: str


def _validation_problems(exc: ValidationError) -> list[dict[str, Any]]:
    return [
        {
            "loc": ["body", *(str(p) for p in error["loc"])],
            "msg": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]


def _free_text_length_problems(free_texts: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "loc": ["body", "free_texts", i],
            "msg": f"el texto supera los {MAX_FREE_TEXT_CHARS} caracteres",
            "type": "value_error",
        }
        for i, text in enumerate(free_texts)
        if len(text) > MAX_FREE_TEXT_CHARS
    ]


def _content_of(parsed: BriefImportIn) -> BriefContent:
    data = parsed.model_dump(mode="json", exclude={"banned_entries", "free_texts"})
    return BriefContent.model_validate(data)


async def import_brief(
    *,
    agent_port: AgentPort,
    telemetry: ObservabilityPort,
    policy: PolicyEngine,
    session_factory: sessionmaker[Session],
    prompt: str,
    user_id: int,
    embedding_model: str,
    max_mandatory_elements: int,
    body: dict[str, Any],
    now: dt.datetime,
) -> ImportResult | ImportRejected | ImportFailure:
    try:
        parsed = BriefImportIn.model_validate(body)
    except ValidationError as exc:
        return ImportRejected(_validation_problems(exc))

    content = _content_of(parsed)
    session = session_factory()
    try:
        db_entries = load_banned_entries(session, user_id, None)
    finally:
        session.close()
    novel_entries = [
        BannedEntry(term=entry.term, type=entry.type, level="novel", keywords=entry.keywords)
        for entry in parsed.banned_entries
    ]
    problems = _free_text_length_problems(parsed.free_texts) + brief_problems(
        content, now.date(), db_entries + novel_entries, [], max_mandatory_elements
    )
    if problems:
        return ImportRejected(problems)

    with unit_of_work(session_factory) as uow:
        novel = Novel(user_id=user_id, title=None, embedding_model=embedding_model, created_at=now)
        uow.add(novel)
        uow.session.flush()
        uow.add(Interview(novel_id=novel.id, created_at=now))
        uow.add(Brief(novel_id=novel.id, content=content.model_dump(mode="json"), status="draft"))
        for entry in parsed.banned_entries:
            add_banned_term(
                uow,
                level="novel",
                user_id=None,
                novel_id=novel.id,
                term=entry.term,
                type_=entry.type,
                keywords=entry.keywords,
            )
        novel_id = novel.id

    for text in parsed.free_texts:
        outcome = await run_free_text(
            agent_port=agent_port,
            telemetry=telemetry,
            policy=policy,
            session_factory=session_factory,
            prompt=prompt,
            novel_id=novel_id,
            user_id=user_id,
            text=text,
            now=now,
            trace_key=import_trace_key(novel_id),
            trace_name=TRACE_NAME,
        )
        if isinstance(outcome, FreeTextFailure):
            return ImportFailure(novel_id=novel_id, reason=outcome.reason)
        _auto_accept(session_factory, [fact.id for fact in outcome.verified_facts])

    with unit_of_work(session_factory) as uow:
        fresh = uow.session.query(Brief).filter(Brief.novel_id == novel_id).one()
        fresh.status = "confirmed"

    with telemetry.trace(
        import_trace_key(novel_id), name=TRACE_NAME, session=str(novel_id)
    ) as trace:
        telemetry.score(trace, "schema-brief", 1)

    return ImportResult(novel_id=novel_id)


def _auto_accept(session_factory: sessionmaker[Session], fact_ids: list[int]) -> None:
    """Los hechos verificados de la importación se aceptan sin cliente y no son obligatorios:
    nadie los marcó (`architecture.md` §3.4, 008-C28)."""
    if not fact_ids:
        return
    with unit_of_work(session_factory) as uow:
        for fact_id in fact_ids:
            fact = uow.session.get(ExtractedFact, fact_id)
            if fact is not None:
                fact.accepted = True

"""Novelas: alta para entrevistar, lista y detalle con estado derivado (008-C01, 008-C02)."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from story_maker.domain.brief import AcceptedFact, BannedEntry, BriefContent
from story_maker.store.models import (
    BannedTerm,
    Brief,
    ExtractedFact,
    FreeText,
    Interview,
    Novel,
    Run,
    Version,
)
from story_maker.store.session import unit_of_work

NovelStatus = Literal["interview", "ready", "in_progress", "published"]
_ACTIVE_RUN_STATUSES = ("queued", "running", "interrupted")


class NovelSummary(BaseModel):
    id: int
    title: str
    recipient_name: str
    status: NovelStatus
    current_version: int | None
    latest_run_id: int | None
    created_at: dt.datetime


def create_interview_novel(
    session_factory: sessionmaker[Session],
    *,
    user_id: int,
    embedding_model: str,
    created_at: dt.datetime,
) -> int:
    """Novela en `interview`, con el brief en borrador y vacío; no abre ninguna sesión (008-C01)."""
    with unit_of_work(session_factory) as uow:
        novel = Novel(
            user_id=user_id, title=None, embedding_model=embedding_model, created_at=created_at
        )
        uow.add(novel)
        uow.session.flush()
        uow.add(Interview(novel_id=novel.id, created_at=created_at))
        uow.add(Brief(novel_id=novel.id, content={}, status="draft"))
        novel_id = novel.id
    return novel_id


def brief_of(session: Session, novel_id: int) -> Brief:
    return session.query(Brief).filter(Brief.novel_id == novel_id).one()


def _status(session: Session, novel: Novel, brief: Brief) -> tuple[NovelStatus, int | None]:
    if brief.status == "draft":
        return "interview", None
    published = [
        v.number
        for v in session.query(Version)
        .filter(Version.novel_id == novel.id, Version.status == "published")
        .all()
        if v.number is not None
    ]
    if published:
        return "published", max(published)
    active = (
        session.query(Run)
        .filter(Run.novel_id == novel.id, Run.status.in_(_ACTIVE_RUN_STATUSES))
        .count()
    )
    if active:
        return "in_progress", None
    return "ready", None


def _latest_run_id(session: Session, novel_id: int) -> int | None:
    """El id de la ejecución más reciente de la novela, de cualquier tipo y estado; ninguno si no
    tiene ninguna (008-C02b, la usa la pantalla de progreso, 025)."""
    run = (
        session.query(Run)
        .filter(Run.novel_id == novel_id)
        .order_by(Run.created_at.desc(), Run.id.desc())
        .first()
    )
    return run.id if run is not None else None


def novel_summary(session: Session, novel: Novel) -> NovelSummary:
    brief = brief_of(session, novel.id)
    status, current_version = _status(session, novel, brief)
    content = BriefContent.model_validate(brief.content) if brief.content else BriefContent()
    return NovelSummary(
        id=novel.id,
        title=novel.title or "",
        recipient_name=content.recipient.name,
        status=status,
        current_version=current_version,
        latest_run_id=_latest_run_id(session, novel.id),
        created_at=novel.created_at,
    )


def list_novels(session: Session, user_id: int) -> list[NovelSummary]:
    novels = (
        session.query(Novel)
        .filter(Novel.user_id == user_id)
        .order_by(Novel.created_at.desc(), Novel.id.desc())
        .all()
    )
    return [novel_summary(session, novel) for novel in novels]


def load_banned_entries(session: Session, user_id: int, novel_id: int | None) -> list[BannedEntry]:
    """Las tres listas que alcanzan a la novela: `global`, `user` del cliente y `novel` de ella
    (`architecture.md` §12.1, 008-C11). Con `novel_id=None` (importación, antes de crear la
    novela), solo trae `global` y `user`: ninguna fila `novel` existe todavía."""
    rows = (
        session.query(BannedTerm)
        .filter(
            (BannedTerm.level == "global")
            | ((BannedTerm.level == "user") & (BannedTerm.user_id == user_id))
            | ((BannedTerm.level == "novel") & (BannedTerm.novel_id == novel_id))
        )
        .all()
    )
    return [
        BannedEntry(
            term=row.term, type=row.type, level=row.level, keywords=list(row.keywords or [])
        )
        for row in rows
    ]


def load_accepted_facts(session: Session, novel_id: int) -> list[AcceptedFact]:
    rows = (
        session.query(ExtractedFact)
        .join(FreeText, ExtractedFact.free_text_id == FreeText.id)
        .filter(FreeText.novel_id == novel_id, ExtractedFact.accepted.is_(True))
        .order_by(ExtractedFact.id)
        .all()
    )
    return [
        AcceptedFact(id=row.id, subject=row.subject, value=row.value, mandatory=row.mandatory)
        for row in rows
    ]


def load_verified_facts(session: Session, novel_id: int) -> list[ExtractedFact]:
    """Los hechos verificados de la novela, con su cita: lo que ve el cliente en el brief
    (008-C18, 008-C22). Un hecho sin verificar no sale nunca (008-I3)."""
    return (
        session.query(ExtractedFact)
        .join(FreeText, ExtractedFact.free_text_id == FreeText.id)
        .filter(FreeText.novel_id == novel_id, ExtractedFact.verified.is_(True))
        .order_by(ExtractedFact.id)
        .all()
    )

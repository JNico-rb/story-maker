"""Turno de la entrevista: abre una sesión del entrevistador, aplica lo que entrega
`update_brief` como parche del borrador y guarda todo si la sesión termina bien
(`architecture.md` §3.1, §3.5; 008-C03 a 008-C08)."""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import NeverFits, NoRoomInTime
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.agents.tools import ToolSpec
from story_maker.domain.brief import (
    BriefContent,
    CloseOne,
    PlotWish,
    Recollection,
    Trait,
    apply_patch,
    missing_fields,
)
from story_maker.interview.banned_terms import add_banned_term
from story_maker.observability.port import ObservabilityPort
from story_maker.store.models import (
    BannedTerm,
    Brief,
    ExtractedFact,
    FreeText,
    Interview,
    InterviewMessage,
)
from story_maker.store.session import unit_of_work

ROLE = "interviewer"


class BannedEntryPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    term: str
    type: Literal["word", "topic"]
    keywords: list[str] = Field(default_factory=list)


class UpdateBriefInput(BaseModel):
    """Lo único que el entrevistador puede entregar: nunca el estado del brief, ni aceptar o
    marcar un hecho, ni quitar una prohibida `novel`, ni tocar las listas `user`/`global`
    (008-C05: esos campos no existen aquí, así que la entrega falla por schema)."""

    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    age: int | None = Field(default=None, ge=0)
    birth_date: dt.date | None = None
    relation: str | None = None
    traits: list[Trait] | None = None
    close_ones: list[CloseOne] | None = None
    recollections: list[Recollection] | None = None
    occasion: Literal["birthday", "wedding", "anniversary", "retirement", "other"] | None = None
    genre: Literal["adventure", "humor", "romance", "mystery", "drama", "fable"] | None = None
    tone: Literal["tender", "funny", "exciting", "nostalgic", "epic", "unsettling"] | None = None
    length: Literal["short", "medium", "long"] | None = None
    dedication: str | None = None
    banned_asked: bool | None = None
    plot_wishes: list[PlotWish] | None = None
    banned_entries: list[BannedEntryPatch] | None = None


UPDATE_BRIEF_TOOL = ToolSpec(
    name="update_brief",
    model=UpdateBriefInput,
    description="Aplica un parche al borrador del brief y, si trae `banned_entries`, las añade "
    "a la lista `novel`.",
    narrative=("dedication",),
)


def interview_trace_key(novel_id: int) -> str:
    """La traza `entrevista` de una novela: la misma clave sigue la misma traza (008-C31)."""
    return f"interview:{novel_id}"


def confirm_brief_status(session_factory: sessionmaker[Session], novel_id: int) -> None:
    """El único escrito de confirmar: entero o nada (008-I5)."""
    with unit_of_work(session_factory) as uow:
        fresh = uow.session.query(Brief).filter(Brief.novel_id == novel_id).one()
        fresh.status = "confirmed"


@dataclass(frozen=True)
class TurnResult:
    reply: str
    content: BriefContent


@dataclass(frozen=True)
class TurnFailure:
    status: int
    reason: str


def _novel_banned_terms(session: Session, novel_id: int) -> list[dict[str, Any]]:
    rows = (
        session.query(BannedTerm)
        .filter(BannedTerm.level == "novel", BannedTerm.novel_id == novel_id)
        .all()
    )
    return [{"term": row.term, "type": row.type, "keywords": row.keywords or []} for row in rows]


def _verified_facts(session: Session, novel_id: int) -> list[dict[str, Any]]:
    rows = (
        session.query(ExtractedFact)
        .join(FreeText, ExtractedFact.free_text_id == FreeText.id)
        .filter(FreeText.novel_id == novel_id, ExtractedFact.verified.is_(True))
        .order_by(ExtractedFact.id)
        .all()
    )
    return [
        {
            "subject": row.subject,
            "attribute": row.attribute,
            "value": row.value,
            "accepted": bool(row.accepted),
            "mandatory": row.mandatory,
        }
        for row in rows
    ]


def _history(session: Session, interview_id: int) -> list[dict[str, str]]:
    rows = (
        session.query(InterviewMessage)
        .filter(InterviewMessage.interview_id == interview_id)
        .order_by(InterviewMessage.id)
        .all()
    )
    return [{"author": row.author, "text": row.text} for row in rows]


def _build_message(
    *,
    history: list[dict[str, str]],
    content: BriefContent,
    novel_banned: list[dict[str, Any]],
    facts: list[dict[str, Any]],
    checks: dict[str, Any],
    client_message: str,
) -> str:
    payload = {
        "history": history,
        "brief": content.model_dump(mode="json"),
        "novel_banned_terms": novel_banned,
        "verified_facts": facts,
        "checks": checks,
        "message": client_message,
    }
    return json.dumps(payload, ensure_ascii=False)


def build_checks(content: BriefContent) -> dict[str, Any]:
    """Las comprobaciones que recibe la sesión, calculadas antes del turno (008-C03)."""
    return {"missing_fields": missing_fields(content)}


async def run_turn(
    *,
    agent_port: AgentPort,
    telemetry: ObservabilityPort,
    session_factory: sessionmaker[Session],
    prompt: str,
    novel_id: int,
    user_id: int,
    text: str,
    now: dt.datetime,
) -> TurnResult | TurnFailure:
    with session_factory() as session:
        interview = session.query(Interview).filter(Interview.novel_id == novel_id).one()
        brief_row = session.query(Brief).filter(Brief.novel_id == novel_id).one()
        content = (
            BriefContent.model_validate(brief_row.content) if brief_row.content else BriefContent()
        )
        message = _build_message(
            history=_history(session, interview.id),
            content=content,
            novel_banned=_novel_banned_terms(session, novel_id),
            facts=_verified_facts(session, novel_id),
            checks=build_checks(content),
            client_message=text,
        )

    with telemetry.trace(
        interview_trace_key(novel_id), name="entrevista", session=str(novel_id)
    ) as trace:
        request = SessionRequest(
            role=ROLE,
            mode=None,
            user_id=user_id,
            novel_id=novel_id,
            prompt=prompt,
            message=message,
            tools=(UPDATE_BRIEF_TOOL,),
            trace=trace,
        )
        try:
            result = await agent_port.run(request)
        except NoRoomInTime:
            # Sin sitio en el techo en `api_wait_seconds`: no se abre sesión (008-C07).
            return TurnFailure(status=503, reason="no_room_in_time")
        except NeverFits:
            # La reserva no cabría ni con el techo entero libre: config inviable (008-C07).
            return TurnFailure(status=422, reason="never_fits")

    if result.outcome != "completed" or result.text is None:
        return TurnFailure(status=503, reason=result.outcome)

    patched = content
    banned_additions: list[BannedEntryPatch] = []
    for call in result.deliveries:
        if call.tool != "update_brief" or call.value is None:
            continue
        value = cast(UpdateBriefInput, call.value)
        patch = value.model_dump(exclude_unset=True, exclude={"banned_entries"})
        patched = apply_patch(patched, patch)
        if "banned_entries" in value.model_fields_set and value.banned_entries:
            banned_additions += value.banned_entries

    with unit_of_work(session_factory) as uow:
        interview_row = uow.session.query(Interview).filter(Interview.novel_id == novel_id).one()
        brief_row = uow.session.query(Brief).filter(Brief.novel_id == novel_id).one()
        uow.add(
            InterviewMessage(
                interview_id=interview_row.id, author="user", text=text, created_at=now
            )
        )
        uow.add(
            InterviewMessage(
                interview_id=interview_row.id,
                author="interviewer",
                text=result.text,
                created_at=now,
            )
        )
        brief_row.content = patched.model_dump(mode="json")
        for entry in banned_additions:
            add_banned_term(
                uow,
                level="novel",
                user_id=None,
                novel_id=novel_id,
                term=entry.term,
                type_=entry.type,
                keywords=entry.keywords,
            )

    return TurnResult(reply=result.text, content=patched)

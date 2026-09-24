"""Audit log de la novela: de solo lectura, para su propietario (008-C27)."""

from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from story_maker.api.dependencies import get_current_user_id
from story_maker.api.ownership import owned_or_404
from story_maker.store.models import AuditLog, Novel

router = APIRouter()


class AuditLogEntryOut(BaseModel):
    created_at: dt.datetime
    origin: Literal[
        "policy_hook",
        "free_text",
        "change_request",
        "manual_edit",
        "publication_gate",
        "mcp_write",
    ]
    decision: Literal["allow", "deny", "flag"]
    rule: str
    role: str | None
    tool: str | None
    run_id: int | None
    detail: list[dict[str, Any]]


@router.get("/api/novels/{novel_id}/audit-log", response_model=list[AuditLogEntryOut])
def get_audit_log(
    novel_id: int, request: Request, user_id: int = Depends(get_current_user_id)
) -> list[AuditLogEntryOut]:
    session = request.app.state.session_factory()
    try:
        owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
        rows = (
            session.query(AuditLog)
            .filter(AuditLog.novel_id == novel_id)
            .order_by(AuditLog.created_at, AuditLog.id)
            .all()
        )
        return [
            AuditLogEntryOut(
                created_at=row.created_at,
                origin=row.origin,
                decision=row.decision,
                rule=row.rule,
                role=row.role,
                tool=row.tool,
                run_id=row.run_id,
                detail=row.detail,
            )
            for row in rows
        ]
    finally:
        session.close()

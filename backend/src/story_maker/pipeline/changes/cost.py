"""Coste de la revisión: las `SesionDeRol` de la propuesta y de la ejecución de cambio de una
`SolicitudDeCambio` (`architecture.md` §13.2, §18; 014-C19)."""

from __future__ import annotations

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from story_maker.store.models import ChangeRequest, RoleSession


def revision_cost(session: Session, request: ChangeRequest) -> float:
    """La suma en USD del coste de las sesiones de su traza de la propuesta y de su ejecución;
    una sesión de la propuesta no tiene ejecución, así que ninguna cuenta dos veces. Un lado
    vacío no filtra nada: `== None` sería `IS NULL` y sumaría sesiones ajenas."""
    links = []
    if request.proposal_trace is not None:
        links.append(RoleSession.trace_id == request.proposal_trace)
    if request.run_id is not None:
        links.append(RoleSession.run_id == request.run_id)
    if not links:
        return 0.0
    total = session.query(func.sum(RoleSession.cost_usd)).filter(or_(*links))
    return float(total.scalar() or 0.0)

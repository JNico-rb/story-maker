"""Sesión del planner en modo `plan`: la tool `submit_plan` y el adaptador de policy con las
prohibidas activas del cliente y de la novela (010-C09).

El puerto de agente (003) ya aplica la lista blanca, el hook de policy y la validación por
schema, y registra la `SesionDeRol`; aquí solo se construye lo propio de la 010: la tool con
sus campos narrativos y la policy de producción, con las prohibidas reales en vez del doble."""

from __future__ import annotations

from typing import cast

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.tools import ToolSpec
from story_maker.pipeline.planning.plan import NARRATIVE_FIELDS, PlanSubmission
from story_maker.policy.audit import record_decision
from story_maker.policy.engine import decide as engine_decide
from story_maker.policy.types import (
    DecisionDePolitica,
    EntradaProhibida,
    NivelProhibida,
    PeticionDePolitica,
    TipoEntrada,
)
from story_maker.store.models import BannedTerm
from story_maker.store.session import unit_of_work

SUBMIT_PLAN = "submit_plan"


def submit_plan_tool() -> ToolSpec:
    """La tool que abre la sesión del planner en modo `plan` (010-C06, 010-C08, 010-C09)."""
    return ToolSpec(
        name=SUBMIT_PLAN,
        model=PlanSubmission,
        description="Entrega el plan de la novela.",
        narrative=NARRATIVE_FIELDS,
    )


class BannedTermsPolicy:
    """`PolicyEngine` de producción para el puerto de agente: decide con el motor de 005 sobre
    las prohibidas activas del cliente y de la novela, y deja cada decisión en el `AuditLog`
    (`architecture.md` §7.5, §12.2; 010-C09)."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def decide(self, peticion: PeticionDePolitica) -> DecisionDePolitica:
        with unit_of_work(self._session_factory) as uow:
            entries = _active_banned_entries(uow.session, peticion)
            decision = engine_decide(peticion.model_copy(update={"banned_entries": entries}))
            record_decision(uow, peticion, decision)
        return decision


def _active_banned_entries(
    session: Session, peticion: PeticionDePolitica
) -> list[EntradaProhibida]:
    """Global, más las de nivel user del cliente y las de nivel novel de la novela."""
    conditions = [BannedTerm.level == "global"]
    if peticion.cliente is not None:
        conditions.append(
            (BannedTerm.level == "user") & (BannedTerm.user_id == int(peticion.cliente))
        )
    if peticion.novela is not None:
        conditions.append(
            (BannedTerm.level == "novel") & (BannedTerm.novel_id == int(peticion.novela))
        )
    rows = session.scalars(select(BannedTerm).where(or_(*conditions))).all()
    return [
        EntradaProhibida(
            term=row.term,
            type=cast(TipoEntrada, row.type),
            level=cast(NivelProhibida, row.level),
            keywords=cast("list[str]", row.keywords) if row.keywords else [],
            owner=_owner(row),
        )
        for row in rows
    ]


def _owner(row: BannedTerm) -> str | None:
    if row.level == "user":
        return str(row.user_id)
    if row.level == "novel":
        return str(row.novel_id)
    return None

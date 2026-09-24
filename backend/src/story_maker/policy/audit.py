"""Registra cada `DecisionDePolitica` en `audit_log`, tabla de solo inserción (architecture.md
§12.2, 005-C19, 005-C20, 005-I2).

`AuditLog.rule` y `.detail` no admiten NULL: una decisión `allow` sin regla ni detalle
(`DecisionDePolitica.rule`/`.detail` en `None`) se registra con la regla vacía (`""`) y el
detalle vacío (`[]`) — la ausencia de causa, no una causa inventada."""

import datetime as dt

from story_maker.policy.types import DecisionDePolitica, PeticionDePolitica
from story_maker.store.models import AuditLog
from story_maker.store.session import UnitOfWork


def record_decision(
    uow: UnitOfWork, peticion: PeticionDePolitica, decision: DecisionDePolitica
) -> AuditLog:
    row = AuditLog(
        user_id=int(peticion.cliente),  # type: ignore[arg-type]
        novel_id=int(peticion.novela) if peticion.novela is not None else None,
        run_id=int(peticion.ejecucion) if peticion.ejecucion is not None else None,
        role=peticion.rol,
        tool=peticion.tool,
        origin=peticion.origen,
        decision=decision.decision,
        rule=decision.rule if decision.rule is not None else "",
        detail=decision.detail if decision.detail is not None else [],
        created_at=dt.datetime.now(dt.UTC),
    )
    uow.add(row)
    return row

"""Una fila `mcp_write` por llamada a una tool de escritura que supera el schema: `allow` si tuvo
efecto, `deny` si no, con el motivo (015-C09, 015-C11 a 015-C14, I8)."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from story_maker.policy.audit import record_decision
from story_maker.policy.types import Decision, DecisionDePolitica, PeticionDePolitica
from story_maker.store.session import unit_of_work


def record_mcp_write(
    session_factory: sessionmaker[Session],
    *,
    user_id: int,
    novel_id: int | None,
    tool: str,
    decision: Decision,
    rule: str | None = None,
    detail: list[dict[str, str]] | None = None,
) -> None:
    peticion = PeticionDePolitica(
        origen="mcp_write",
        cliente=str(user_id),
        novela=str(novel_id) if novel_id is not None else None,
        tool=tool,
    )
    resolved = DecisionDePolitica(decision=decision, rule=rule, detail=detail)
    with unit_of_work(session_factory) as uow:
        record_decision(uow, peticion, resolved)

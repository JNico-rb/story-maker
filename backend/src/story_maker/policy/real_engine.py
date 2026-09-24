"""Adaptador real del `MotorDePoliticas` para el puerto de agente (aviso de `TODO.md`: lo cablea
008, que abre las primeras sesiones reales — entrevistador y extractor — y lo reutiliza 011).

Carga las prohibidas del cliente y de la novela desde `banned_terms` (más las `global`, siempre),
decide con `policy.engine.decide` (005) y registra la decisión en el audit log, todo en una misma
unidad de trabajo. Patrón: `RealEngine` de `tests/agents/test_port.py` (carril-b), que hace lo
mismo con una lista fija en vez de leer la base."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from story_maker.policy.audit import record_decision
from story_maker.policy.engine import decide
from story_maker.policy.types import DecisionDePolitica, EntradaProhibida, PeticionDePolitica
from story_maker.store.models import BannedTerm
from story_maker.store.session import unit_of_work


def _owner(row: BannedTerm) -> str | None:
    if row.level == "user":
        return str(row.user_id)
    if row.level == "novel":
        return str(row.novel_id)
    return None


def _load_banned_entries(session: Session, peticion: PeticionDePolitica) -> list[EntradaProhibida]:
    """Las `global`, las `user` del cliente de la petición y las `novel` de su novela."""
    query = session.query(BannedTerm).filter(
        (BannedTerm.level == "global")
        | ((BannedTerm.level == "user") & (BannedTerm.user_id == _as_int(peticion.cliente)))
        | ((BannedTerm.level == "novel") & (BannedTerm.novel_id == _as_int(peticion.novela)))
    )
    return [
        EntradaProhibida(
            term=row.term,
            type=row.type,
            level=row.level,
            keywords=list(row.keywords or []),
            owner=_owner(row),
        )
        for row in query.all()
    ]


def _as_int(value: str | None) -> int | None:
    return int(value) if value is not None else None


class RealPolicyEngine:
    """`PolicyEngine` real: prohibidas de SQLite + `policy.engine.decide` + audit log."""

    def __init__(self, session_factory: sessionmaker[Session], base_url: str | None) -> None:
        self._session_factory = session_factory
        self._base_url = base_url

    def decide(self, peticion: PeticionDePolitica) -> DecisionDePolitica:
        with unit_of_work(self._session_factory) as uow:
            entries = _load_banned_entries(uow.session, peticion)
            with_entries = peticion.model_copy(update={"banned_entries": entries})
            decision = decide(with_entries, base_url=self._base_url)
            record_decision(uow, peticion, decision)
        return decision

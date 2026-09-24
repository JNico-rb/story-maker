"""Las pasadas del `MotorDePoliticas` de una solicitud de cambio: sobre la petición y sobre cada
valor nuevo, con origen `change_request` (`architecture.md` §12.1, §12.2; 014-I11).

Cada pasada deja su decisión en el audit log, con la ubicación de la coincidencia, y su span
`validador:palabras-prohibidas` con su score en la traza `propuesta-de-cambio` (014-C04)."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from story_maker.observability.port import ObservabilityPort, Trace
from story_maker.pipeline.planning.session import _active_banned_entries
from story_maker.policy.audit import record_decision
from story_maker.policy.engine import decide
from story_maker.policy.types import CampoNarrativo, DecisionDePolitica, PeticionDePolitica
from story_maker.store.session import unit_of_work

BANNED_TERMS = "palabras-prohibidas"


def judge_text(
    session_factory: sessionmaker[Session],
    telemetry: ObservabilityPort,
    trace: Trace,
    *,
    user_id: int,
    novel_id: int,
    location: str,
    text: str,
) -> DecisionDePolitica:
    peticion = PeticionDePolitica(
        origen="change_request",
        cliente=str(user_id),
        novela=str(novel_id),
        campos=[CampoNarrativo(path=location, texto=text, narrativo=True)],
    )
    with unit_of_work(session_factory) as uow:
        entries = _active_banned_entries(uow.session, peticion)
        decision = decide(peticion.model_copy(update={"banned_entries": entries}))
        if decision.detail:
            located = [{**item, "location": location} for item in decision.detail]
            decision = decision.model_copy(update={"detail": located})
        record_decision(uow, peticion, decision)
    denied = decision.decision == "deny"
    with telemetry.span(trace, f"validador:{BANNED_TERMS}") as span:
        comment = match_text(decision) if denied else None
        telemetry.score(trace, BANNED_TERMS, 0 if denied else 1, comment=comment, span=span)
    if decision.decision == "flag":
        # La inyección se marca y no deniega (014-C05, `architecture.md` §12.4).
        phrases = "; ".join(item.get("phrase", "") for item in decision.detail or [])
        with telemetry.span(trace, f"politica:{decision.rule}", level="WARNING", reason=phrases):
            pass
    return decision


def match_text(decision: DecisionDePolitica) -> str:
    """Término, nivel y variante de la coincidencia, en una línea."""
    item = (decision.detail or [{}])[0]
    return f"término={item.get('term')}, nivel={item.get('level')}, variante={item.get('variant')}"

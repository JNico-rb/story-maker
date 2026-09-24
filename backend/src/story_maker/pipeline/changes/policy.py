"""Las pasadas del `MotorDePoliticas` de una solicitud de cambio: sobre la petición y sobre cada
valor nuevo, con origen `change_request` (`architecture.md` §12.1, §12.2; 014-I11).

Cada pasada deja su decisión en el audit log y su span `validador:palabras-prohibidas` con su
score en la traza `propuesta-de-cambio` (014-C19)."""

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
    path: str,
    text: str,
) -> DecisionDePolitica:
    peticion = PeticionDePolitica(
        origen="change_request",
        cliente=str(user_id),
        novela=str(novel_id),
        campos=[CampoNarrativo(path=path, texto=text, narrativo=True)],
    )
    with unit_of_work(session_factory) as uow:
        entries = _active_banned_entries(uow.session, peticion)
        decision = decide(peticion.model_copy(update={"banned_entries": entries}))
        record_decision(uow, peticion, decision)
    with telemetry.span(trace, f"validador:{BANNED_TERMS}") as span:
        telemetry.score(trace, BANNED_TERMS, 1, span=span)
    return decision

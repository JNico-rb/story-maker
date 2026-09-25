"""011-I1 (segunda mitad): dentro de una ejecución hay como mucho una sesión de rol abierta a la
vez. Se registra la apertura (`FakeAgent.open`) y el cierre (`disconnect`, siempre llamado por
`AgentPort._drive`, tanto si la sesión termina normal como si se corta) de cada sesión de una
generación completa — sus diez capítulos, escritos con el doble falso — y se comprueba que
nunca hay más de una abierta a la vez."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import PhaseDouble, Seed, script_accepted_chapters

from story_maker.agents.fake import FakeAgent, FakeSession
from story_maker.agents.port import SessionRequest
from story_maker.agents.profiles import RoleProfile
from story_maker.observability.port import Trace
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import Production
from story_maker.store.models import Chapter


@dataclass
class SessionLedger:
    events: list[tuple[str, str]] = field(default_factory=list)
    current: int = 0
    max_concurrent: int = 0


class RecordingAgent:
    """Envuelve el doble falso para contar sesiones abiertas y cerradas a la vez, sin cambiar su
    comportamiento (011-I1)."""

    def __init__(self, inner: FakeAgent, ledger: SessionLedger) -> None:
        self._inner = inner
        self._ledger = ledger

    def script(self, role: str, mode: str | None, script: object) -> None:
        self._inner.script(role, mode, script)  # type: ignore[arg-type]

    def prepare(self, request: SessionRequest) -> None:
        self._inner.prepare(request)

    def open(self, request: SessionRequest, profile: RoleProfile, hooks: object) -> FakeSession:
        session = self._inner.open(request, profile, hooks)  # type: ignore[arg-type]
        ledger = self._ledger
        ledger.current += 1
        ledger.max_concurrent = max(ledger.max_concurrent, ledger.current)
        ledger.events.append(("open", request.role))
        original_disconnect = session.disconnect

        async def disconnect() -> None:
            await original_disconnect()
            ledger.current -= 1
            ledger.events.append(("close", request.role))

        session.disconnect = disconnect  # type: ignore[method-assign]
        return session

    @property
    def sessions(self) -> list[FakeSession]:
        return self._inner.sessions


@pytest.fixture
def ledger() -> SessionLedger:
    return SessionLedger()


@pytest.fixture
def fake(ledger: SessionLedger) -> RecordingAgent:
    return RecordingAgent(FakeAgent(), ledger)


async def test_a_complete_generation_never_has_two_role_sessions_open_at_once(
    production: Production,
    planning: PhaseDouble,
    fake: RecordingAgent,
    ledger: SessionLedger,
    seed: Seed,
    session_factory: sessionmaker[Session],
) -> None:
    gate_calls: list[int] = []

    async def gate_stub(run_id: int, trace: Trace) -> None:
        gate_calls.append(run_id)

    orchestrator = Orchestrator(production=production, planning=planning, gate=gate_stub)
    script_accepted_chapters(fake, 10)  # type: ignore[arg-type]

    await orchestrator.execute(seed.run_id)

    assert gate_calls == [seed.run_id]  # llegó al gate: los diez capítulos se escribieron
    with session_factory() as session:
        assert session.query(Chapter).filter_by(version_id=seed.version_id).count() == 10

    assert (
        len(ledger.events) == 40
    )  # apertura y cierre de una sesión del writer y una del editor por capítulo
    assert ledger.max_concurrent == 1
    assert ledger.current == 0  # todas cerraron

    # Cada apertura tiene su cierre antes de la siguiente apertura: nunca se solapan.
    opens = 0
    for kind, _role in ledger.events:
        if kind == "open":
            opens += 1
            assert opens == 1
        else:
            opens -= 1
            assert opens == 0

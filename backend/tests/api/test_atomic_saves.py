"""Un turno, una extracción, una confirmación y una importación se guardan enteros o no se
guardan (008-I5): un fallo del store simulado a mitad de cada guardado no deja nada de él."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, FakeAgent, Say, Script
from story_maker.agents.port import AgentPort
from story_maker.interview.brief import confirm_brief_status, run_turn
from story_maker.interview.free_text import run_free_text
from story_maker.interview.import_brief import import_brief
from story_maker.observability.null import NullObservability
from story_maker.policy.real_engine import RealPolicyEngine
from story_maker.store import session as session_module
from story_maker.store.models import Brief, ExtractedFact, FreeText, InterviewMessage, Novel, User

from .briefs import B0_CONTENT, seed_brief
from .test_free_text_extraction import FACTS, LETTER

NOW = dt.datetime(2026, 9, 24, 12, 0)


def _inject_fault_mid_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cada guardado hace `flush()` (algo llegó a escribirse en la transacción) y luego falla
    antes del `commit()` real: nada de eso debe sobrevivir a `session.close()` (rollback
    implícito de SQLAlchemy, `store/session.py`). Se activa después de la siembra de cada
    prueba, para que solo falle el guardado bajo prueba, no la siembra misma."""

    def failing_commit(self: session_module.UnitOfWork) -> None:
        self.session.flush()
        raise RuntimeError("fallo inyectado a mitad del guardado")

    monkeypatch.setattr(session_module.UnitOfWork, "commit", failing_commit)


def _user_id(session_factory: sessionmaker[Session]) -> int:
    with session_factory() as session:
        return session.query(User).one().id


async def test_a_fault_mid_turn_leaves_no_message_and_no_brief_change(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
    agent_port: AgentPort,
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    user_id = _user_id(session_factory)
    fake.script(
        "interviewer",
        None,
        Script(steps=(Call("update_brief", {"name": "Marta", "age": 40}), Say("¿Y luego?"))),
    )
    prompt = (workspace / "prompts" / "interviewer.md").read_text(encoding="utf-8")
    _inject_fault_mid_commit(monkeypatch)

    with pytest.raises(RuntimeError):
        await run_turn(
            agent_port=agent_port,
            telemetry=NullObservability(),
            session_factory=session_factory,
            prompt=prompt,
            novel_id=novel_id,
            user_id=user_id,
            text="hola",
            now=NOW,
        )

    with session_factory() as session:
        assert session.query(InterviewMessage).count() == 0
        brief = session.query(Brief).filter(Brief.novel_id == novel_id).one()
        assert brief.content == {}


async def test_a_fault_mid_extraction_leaves_no_free_text_and_no_fact(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
    agent_port: AgentPort,
    policy: RealPolicyEngine,
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)
    user_id = _user_id(session_factory)
    fake.script(
        "extractor",
        None,
        Script(steps=(Call("submit_facts", {"facts": FACTS, "discarded_instructions": []}),)),
    )
    prompt = (workspace / "prompts" / "extractor.md").read_text(encoding="utf-8")
    _inject_fault_mid_commit(monkeypatch)

    with pytest.raises(RuntimeError):
        await run_free_text(
            agent_port=agent_port,
            telemetry=NullObservability(),
            policy=policy,
            session_factory=session_factory,
            prompt=prompt,
            novel_id=novel_id,
            user_id=user_id,
            text=LETTER,
            now=NOW,
        )

    with session_factory() as session:
        assert session.query(FreeText).filter(FreeText.novel_id == novel_id).count() == 0
        assert session.query(ExtractedFact).count() == 0


def test_a_fault_mid_confirmation_leaves_the_brief_a_draft(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)
    _inject_fault_mid_commit(monkeypatch)

    with pytest.raises(RuntimeError):
        confirm_brief_status(session_factory, novel_id)

    with session_factory() as session:
        brief = session.query(Brief).filter(Brief.novel_id == novel_id).one()
        assert brief.status == "draft"


async def test_a_fault_mid_import_creation_leaves_no_novel(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    agent_port: AgentPort,
    policy: RealPolicyEngine,
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = _user_id(session_factory)
    prompt = (workspace / "prompts" / "extractor.md").read_text(encoding="utf-8")
    _inject_fault_mid_commit(monkeypatch)

    with pytest.raises(RuntimeError):
        await import_brief(
            agent_port=agent_port,
            telemetry=NullObservability(),
            policy=policy,
            session_factory=session_factory,
            prompt=prompt,
            user_id=user_id,
            embedding_model="M1",
            max_mandatory_elements=8,
            body=dict(B0_CONTENT),  # sin `free_texts`: solo se ejercita la creación atómica
            now=NOW,
        )

    with session_factory() as session:
        assert session.query(Novel).count() == 0

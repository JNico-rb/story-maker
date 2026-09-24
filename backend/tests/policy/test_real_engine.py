"""Adaptador real del `MotorDePoliticas` (aviso de `TODO.md`, carril-b/008): carga las prohibidas
del cliente y de la novela desde SQLite, decide como 005 y registra en el audit log."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from story_maker.policy.real_engine import RealPolicyEngine
from story_maker.policy.types import PeticionDePolitica
from story_maker.store.models import AuditLog, BannedTerm, Novel, User
from story_maker.store.session import create_schema, make_engine, make_session_factory

NOW = dt.datetime(2026, 9, 24, 12, 0)


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    eng = make_engine(tmp_path / "story-maker.db")
    create_schema(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Session]:
    return make_session_factory(engine)


@pytest.fixture
def two_clients(session_factory: sessionmaker[Session]) -> tuple[int, int, int, int]:
    """Dos clientes, cada uno con su novela: A tiene una prohibida `user`, su novela una `novel`."""
    with session_factory() as session:
        a = User(email="a@example.com", password_hash="x", created_at=NOW)
        b = User(email="b@example.com", password_hash="x", created_at=NOW)
        session.add_all([a, b])
        session.flush()
        novel_a = Novel(user_id=a.id, title=None, embedding_model="m", created_at=NOW)
        novel_b = Novel(user_id=b.id, title=None, embedding_model="m", created_at=NOW)
        session.add_all([novel_a, novel_b])
        session.flush()
        session.add_all(
            [
                BannedTerm(
                    level="global",
                    user_id=None,
                    novel_id=None,
                    term="idiota",
                    type="word",
                    keywords=None,
                    normalized="idiota",
                ),
                BannedTerm(
                    level="user",
                    user_id=a.id,
                    novel_id=None,
                    term="expareja",
                    type="word",
                    keywords=None,
                    normalized="expareja",
                ),
                BannedTerm(
                    level="novel",
                    user_id=None,
                    novel_id=novel_a.id,
                    term="pedro",
                    type="word",
                    keywords=None,
                    normalized="pedro",
                ),
            ]
        )
        session.commit()
        return a.id, novel_a.id, b.id, novel_b.id


def _peticion(cliente: int, novela: int, texto: str) -> PeticionDePolitica:
    from story_maker.policy.types import CampoNarrativo

    return PeticionDePolitica(
        origen="policy_hook",
        cliente=str(cliente),
        novela=str(novela),
        rol="writer",
        tool="submit_chapter",
        campos=[CampoNarrativo(path="text", narrativo=True, texto=texto)],
    )


def test_loads_global_and_the_client_and_novel_scoped_banned_terms(
    session_factory: sessionmaker[Session], two_clients: tuple[int, int, int, int]
) -> None:
    client_a, novel_a, _client_b, _novel_b = two_clients
    engine_under_test = RealPolicyEngine(session_factory, base_url=None)

    global_hit = engine_under_test.decide(_peticion(client_a, novel_a, "Era un idiota."))
    user_hit = engine_under_test.decide(_peticion(client_a, novel_a, "Habla de mi expareja."))
    novel_hit = engine_under_test.decide(_peticion(client_a, novel_a, "Vino Pedro a la fiesta."))
    clean = engine_under_test.decide(_peticion(client_a, novel_a, "Un día tranquilo."))

    assert [d.decision for d in (global_hit, user_hit, novel_hit, clean)] == [
        "deny",
        "deny",
        "deny",
        "allow",
    ]


def test_a_banned_term_of_one_client_never_reaches_another_clients_novel(
    session_factory: sessionmaker[Session], two_clients: tuple[int, int, int, int]
) -> None:
    client_a, novel_a, client_b, novel_b = two_clients
    engine_under_test = RealPolicyEngine(session_factory, base_url=None)
    del client_a, novel_a

    decision = engine_under_test.decide(_peticion(client_b, novel_b, "Habla de mi expareja."))

    assert decision.decision == "allow"


def test_every_decision_is_recorded_in_the_audit_log(
    session_factory: sessionmaker[Session], two_clients: tuple[int, int, int, int]
) -> None:
    client_a, novel_a, _client_b, _novel_b = two_clients
    engine_under_test = RealPolicyEngine(session_factory, base_url=None)

    engine_under_test.decide(_peticion(client_a, novel_a, "Era un idiota."))

    with session_factory() as session:
        rows = session.query(AuditLog).filter(AuditLog.user_id == client_a).all()
        assert len(rows) == 1
        assert rows[0].decision == "deny"
        assert rows[0].origin == "policy_hook"
        assert rows[0].novel_id == novel_a

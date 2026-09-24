"""`GET /api/novels/{id}/story-bible?version={v}` (009-C25 a 009-C27)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.api.app import create_app
from story_maker.store.brief_canon import (
    BriefCloseOne,
    BriefRecipient,
    BriefRecollection,
    BriefTrait,
    ConfirmedBrief,
    create_generation_candidate,
)
from story_maker.store.models import Fact, Novel, Version
from story_maker.store.session import create_schema, make_engine, make_session_factory, unit_of_work
from story_maker.store.story_bible import change_fact_value, read_story_bible
from story_maker.store.version_copy import copy_version
from story_maker.store.versions import publish

JWT_SECRET = "x" * 32
NOW = dt.datetime(2026, 9, 24, 11, 0)
BRIEF = ConfirmedBrief(
    recipient=BriefRecipient(
        "Marta", 40, name_element_id=1, traits=(BriefTrait("curiosa", 2, mandatory=False),)
    ),
    close_ones=(BriefCloseOne("Toby", "perro", "animal", element_id=3, mandatory=True),),
    recollections=(
        BriefRecollection(
            "se perdió en la feria de su pueblo",
            "la feria del pueblo",
            element_id=4,
            mandatory=True,
            age=8,
        ),
    ),
)


@pytest.fixture
def session_factory(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = make_engine(tmp_path / "story-maker.db")
    create_schema(engine)
    yield make_session_factory(engine)
    engine.dispose()


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> TestClient:
    return TestClient(create_app(session_factory=session_factory, jwt_secret=JWT_SECRET))


def _client_token(client: TestClient, email: str) -> tuple[int, dict[str, str]]:
    body = {"email": email, "password": "contraseña-1"}
    user_id = client.post("/api/auth/register", json=body).json()["id"]
    token = client.post("/api/auth/login", json=body).json()["access_token"]
    return user_id, {"Authorization": f"Bearer {token}"}


@dataclass(frozen=True)
class N1:
    novel_id: int
    v1: int
    v2: int
    candidate: int


def _toby_name_fact(session: Session, version_id: int) -> Fact:
    return (
        session.query(Fact).filter_by(version_id=version_id, attribute="name", value="Toby").one()
    )


def _seed_n1(session_factory: sessionmaker[Session], user_id: int) -> N1:
    """N1 con v1, v2 (Toby pasa a «Nala») y una candidata abierta (Nala pasa a «Kira»)."""
    with unit_of_work(session_factory) as uow:
        novel = Novel(user_id=user_id, title=None, embedding_model="m1", created_at=NOW)
        uow.add(novel)
        uow.session.flush()
        v1 = create_generation_candidate(uow, novel.id, BRIEF, now=NOW)
        publish(uow, v1.id, pdf_path="v1.pdf", now=NOW)
    with unit_of_work(session_factory) as uow:
        v2 = copy_version(uow, v1.id, now=NOW).version
        change_fact_value(uow, _toby_name_fact(uow.session, v2.id).id, "Nala")
    with unit_of_work(session_factory) as uow:
        publish(uow, v2.id, pdf_path="v2.pdf", now=NOW)
    with unit_of_work(session_factory) as uow:
        candidate = copy_version(uow, v2.id, now=NOW).version
        nala = uow.session.query(Fact).filter_by(version_id=candidate.id, value="Nala").one()
        change_fact_value(uow, nala.id, "Kira")
    return N1(novel.id, v1.id, v2.id, candidate.id)


def _expected(session_factory: sessionmaker[Session], version_id: int) -> object:
    with session_factory() as session:
        return jsonable_encoder(read_story_bible(session, version_id))


def _names(story_bible: dict[str, object]) -> set[str]:
    characters = story_bible["characters"]
    assert isinstance(characters, list)
    return {c["canonical_name"] for c in characters}


def test_the_api_returns_the_story_bible_of_the_current_version(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id, headers = _client_token(client, "cliente-a@example.com")
    n1 = _seed_n1(session_factory, user_id)

    response = client.get(f"/api/novels/{n1.novel_id}/story-bible", headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["version"] == 2
    assert body["story_bible"] == _expected(session_factory, n1.v2)
    assert _names(body["story_bible"]) == {"Marta", "Nala"}
    name_facts = [f["value"] for f in body["story_bible"]["facts"] if f["attribute"] == "name"]
    assert sorted(name_facts) == ["Marta", "Nala"]
    assert "Kira" not in response.text
    with session_factory() as session:
        assert session.get(Version, n1.candidate).status == "candidate"

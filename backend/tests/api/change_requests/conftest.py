"""Fixture común F de la 014 (`specs/backend/014-cambios-del-lector.md`, «Fixture común»): una
novela del cliente A con v1 publicada, creada directamente en el store y con los dobles.

- El perro «Toby»: hecho de nombre de origen brief, con `UsoDeHecho` en 2 y 5; literal en el
  texto de 2, 5 y 7 (el 7 sin uso registrado); presente en un evento registrado del 9, sin nombre.
- El destinatario «Ada»: aparece en los diez capítulos (usos de su nombre) y tiene el hecho del
  postre favorito, «tarta de manzana», con uso en el 3.
- Un hecho inventado sin usos ni aparición literal.
- Prohibidas: global «zoquete», user del cliente A «hospital», novel «marta» y user del cliente B
  «playa».

Cada variación de una tabla de la spec se construye con `build_f(..., extra_text=..., titles=...)`
antes de publicar v1: una versión publicada ya no admite escrituras."""

from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import itertools
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import Call, FakeAgent, Script
from story_maker.agents.port import AgentPort
from story_maker.api.app import create_app
from story_maker.api.auth import create_access_token
from story_maker.config import Config
from story_maker.domain.banned_terms import normalize_token
from story_maker.observability.null import NullObservability
from story_maker.policy.real_engine import RealPolicyEngine
from story_maker.store import models
from story_maker.store.brief_canon import (
    BriefCloseOne,
    BriefRecipient,
    ConfirmedBrief,
    create_generation_candidate,
)
from story_maker.store.session import unit_of_work
from story_maker.store.version_copy import copy_version
from story_maker.store.versions import publish

JWT_SECRET = "x" * 32
NOW = dt.datetime(2026, 9, 24, 12, 0, 0)
PLANNER_CHANGE_PROMPT = "prompts/planner-change.md"

_emails = itertools.count(1)


class MutableClock:
    """Reloj controlable de la config de prueba (F): `advance` lo mueve."""

    def __init__(self, now: dt.datetime) -> None:
        self.now = now

    def __call__(self) -> dt.datetime:
        return self.now

    def advance(self, **delta: float) -> None:
        self.now = self.now + dt.timedelta(**delta)


@dataclass(frozen=True)
class F:
    novel_id: int
    user_a: int
    user_b: int
    v1_id: int
    ada_id: int
    toby_id: int
    toby_name_fact: int
    dessert_fact: int
    invented_fact: int
    park_id: int


def chapter_text(number: int) -> str:
    text = f"Capítulo {number}. Ada camina por la ciudad."
    if number in (2, 5, 7):
        text += " Toby ladra a su lado."
    return text


def build_f(
    session_factory: sessionmaker[Session],
    *,
    extra_text: dict[int, str] | None = None,
    titles: dict[int, str] | None = None,
) -> F:
    extra_text = extra_text or {}
    titles = titles or {}
    with unit_of_work(session_factory) as uow:
        user_a = models.User(
            email=f"a-{next(_emails)}@example.com", password_hash="h", created_at=NOW
        )
        user_b = models.User(
            email=f"b-{next(_emails)}@example.com", password_hash="h", created_at=NOW
        )
        uow.add(user_a)
        uow.add(user_b)
        uow.session.flush()
        novel = models.Novel(
            user_id=user_a.id, title="La aventura de Ada", embedding_model="M1", created_at=NOW
        )
        uow.add(novel)
        uow.session.flush()
        uow.add(models.Brief(novel_id=novel.id, content={}, status="confirmed"))
        for level, term, owner in (
            ("global", "zoquete", {}),
            ("user", "hospital", {"user_id": user_a.id}),
            ("novel", "marta", {"novel_id": novel.id}),
            ("user", "playa", {"user_id": user_b.id}),
        ):
            uow.add(
                models.BannedTerm(
                    level=level,
                    term=term,
                    type="word",
                    keywords=None,
                    normalized=normalize_token(term),
                    **owner,
                )
            )
        novel_id, a_id, b_id = novel.id, user_a.id, user_b.id

    brief = ConfirmedBrief(
        recipient=BriefRecipient("Ada", 30, name_element_id=1, traits=()),
        close_ones=(BriefCloseOne("Toby", "perro", "animal", element_id=2, mandatory=True),),
    )
    with unit_of_work(session_factory) as uow:
        v1_id = create_generation_candidate(uow, novel_id, brief, now=NOW).id

    with unit_of_work(session_factory) as uow:
        session = uow.session
        ada = _character(session, v1_id, "Ada")
        toby = _character(session, v1_id, "Toby")
        ada_name = _name_fact(session, v1_id, ada.id)
        toby_name = _name_fact(session, v1_id, toby.id)
        dessert = models.Fact(
            version_id=v1_id,
            subject_type="character",
            character_id=ada.id,
            attribute="trait",
            value="tarta de manzana",
            origin="brief",
            mandatory=False,
            personal_element_id=3,
        )
        invented = models.Fact(
            version_id=v1_id,
            subject_type="character",
            character_id=toby.id,
            attribute="trait",
            value="come zanahorias",
            origin="invented",
            mandatory=False,
        )
        park = models.Place(
            version_id=v1_id, canonical_name="el parque", description="", origin="invented"
        )
        uow.add(dessert)
        uow.add(invented)
        uow.add(park)
        session.flush()
        for n in range(1, 11):
            uow.add(models.FactUsage(fact_id=ada_name.id, chapter=n))
        for n in (2, 5):
            uow.add(models.FactUsage(fact_id=toby_name.id, chapter=n))
        uow.add(models.FactUsage(fact_id=dessert.id, chapter=3))
        event = models.Event(
            version_id=v1_id,
            statement="Ada pasea por el parque",
            moment=dt.datetime(2026, 5, 1, 10, 0),
            place_id=park.id,
            type="ordinary",
            analepsis=False,
            origin="recorded",
            chapter=9,
            beat=1,
        )
        uow.add(event)
        session.flush()
        uow.add(models.EventCharacter(event_id=event.id, character_id=ada.id))
        uow.add(models.EventCharacter(event_id=event.id, character_id=toby.id))
        for n in range(1, 11):
            title = titles.get(n, f"Capítulo {n}")
            text = chapter_text(n) + extra_text.get(n, "")
            uow.add(
                models.Chapter(
                    version_id=v1_id,
                    number=n,
                    title=title,
                    text=text,
                    summary=f"Resumen {n}",
                    word_count=1200,
                    content_hash=hashlib.sha256(f"{title}\n{text}".encode()).hexdigest(),
                )
            )
        ids = (ada.id, toby.id, toby_name.id, dessert.id, invented.id, park.id)

    with unit_of_work(session_factory) as uow:
        publish(uow, v1_id, pdf_path="v1.pdf", now=NOW)

    return F(novel_id, a_id, b_id, v1_id, *ids)


def publish_copy(session_factory: sessionmaker[Session], base_id: int) -> int:
    """Publica una copia sin cambios de `base_id`: la base deja de ser la vigente."""
    with unit_of_work(session_factory) as uow:
        version_id = copy_version(uow, base_id, now=NOW).version.id
    with unit_of_work(session_factory) as uow:
        publish(uow, version_id, pdf_path="v2.pdf", now=NOW)
    return version_id


def _character(session: Session, version_id: int, name: str) -> models.Character:
    return (
        session.query(models.Character).filter_by(version_id=version_id, canonical_name=name).one()
    )


def _name_fact(session: Session, version_id: int, character_id: int) -> models.Fact:
    return (
        session.query(models.Fact)
        .filter_by(version_id=version_id, character_id=character_id, attribute="name")
        .one()
    )


def headers(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id, JWT_SECRET, 24, NOW)}"}


def fact_selection(fact_id: int) -> dict[str, Any]:
    return {"type": "fact", "fact_id": fact_id}


def fragment_selection(chapter: int, quote: str | None = None, version: int = 1) -> dict[str, Any]:
    return {
        "type": "fragment",
        "version": version,
        "chapter": chapter,
        "quote": quote if quote is not None else "Ada camina por la ciudad.",
    }


def rename(fact_id: int, value: str) -> dict[str, Any]:
    return {"changes": [{"fact_id": fact_id, "new_value": value}]}


def propose(fake: FakeAgent, *proposals: dict[str, Any]) -> None:
    """Un guion del planner en modo cambio por sesión, cada uno con su entrega."""
    for proposal in proposals:
        fake.script("planner", "change", Script(steps=(Call("propose_change", proposal),)))


def planner_message(fake: FakeAgent, index: int = 0) -> dict[str, Any]:
    sessions = [s for s in fake.sessions if s.request.role == "planner"]
    return json.loads(sessions[index].request.message)  # type: ignore[no-any-return]


@pytest.fixture
def clock() -> MutableClock:
    return MutableClock(NOW)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    path = tmp_path / "harness_workspace"
    (path / "prompts").mkdir(parents=True)
    (path / "CLAUDE.md").write_text("Escribe en español.", encoding="utf-8")
    (path / PLANNER_CHANGE_PROMPT).write_text("Eres el planner en modo cambio.", encoding="utf-8")
    return path


@pytest.fixture
def f(session_factory: sessionmaker[Session]) -> F:
    return build_f(session_factory)


ClientBuilder = Callable[[Config], tuple[TestClient, TokenCeiling]]


@pytest.fixture
def build_client(
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
    telemetry: NullObservability,
    workspace: Path,
    clock: MutableClock,
) -> ClientBuilder:
    """Una app con otra config (techo, espera, límites de sesión) sobre los mismos dobles."""

    def build(config: Config) -> tuple[TestClient, TokenCeiling]:
        ceiling = TokenCeiling(config.token_ceiling)
        policy = RealPolicyEngine(session_factory, base_url="http://127.0.0.1:8000")
        port = AgentPort(
            agent=fake,
            config=config,
            ceiling=ceiling,
            policy=policy,
            telemetry=telemetry,
            session_factory=session_factory,
            workspace=workspace,
        )
        app = create_app(
            session_factory=session_factory,
            jwt_secret=JWT_SECRET,
            clock=clock,
            agent_port=port,
            telemetry=telemetry,
            config=config,
            workspace=workspace,
            policy=policy,
        )
        return TestClient(app), ceiling

    return build


def with_planner_turns(config: Config, max_turns: int) -> Config:
    roles = dict(config.roles)
    roles["planner"] = dataclasses.replace(roles["planner"], max_turns=max_turns)
    return dataclasses.replace(config, roles=roles)

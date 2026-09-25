"""Fixtures de la edición manual (019), con las convenciones de la spec: el cliente A tiene la
novela N con v1 publicada y vigente, y el año presente es 2026.

- Marta, la destinataria, nació el 15-06-1990. Su perro Toby no tiene fecha de nacimiento; su
  hecho de nombre tiene `UsoDeHecho` en los capítulos 1, 3 y 7, y «Toby» es literal en ellos.
- Rosa, excluida por un evento de origen brief (2010); Luis, por uno registrado en el capítulo 2
  (febrero de 2026); Ana, por uno registrado en el 6 (agosto de 2026); Pablo, solo en un evento
  planificado.
- El recuerdo obligatorio «el viaje a Cádiz», asignado por el outline solo al capítulo 3, con su
  único `UsoDeHecho` en él.
- Los eventos registrados del capítulo 3 son de marzo de 2026; los del 8, una analepsis, de 2005;
  el 9 no tiene ninguno.
- «IA» aparece en el capítulo 1 y «entonces» en el 2; «Pepe» y «Nala», en ninguno.
- Prohibidas: global «zoquete» (el insulto de prueba), user de A «tabaco», novel de N «Jorge» y
  user de otro cliente B «mar».

Los capítulos de v1 son textos limpios: frases de diez palabras de dos sílabas que no se repiten
en un párrafo, sin signos de diálogo ni primera persona, así que ningún linter de 018 avisa. Los
roles corren en el doble falso; Langfuse, en el doble nulo; el `VerificadorFormal`, en el doble
programado del gate. Umbrales en 3 y `max_retries.chapter` = 3."""

from __future__ import annotations

import dataclasses
import datetime as dt
import itertools
from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.changes.conftest import real_cards
from tests.pipeline.conftest import NOW, PhaseDouble, Seed, seed_user
from tests.pipeline.gate.conftest import GateKit, make_kit, seed_world

from story_maker.agents.port import AgentPort
from story_maker.api.app import create_app
from story_maker.api.auth import create_access_token
from story_maker.config import Config
from story_maker.domain.banned_terms import normalize_token
from story_maker.domain.constants import RECOLLECTION
from story_maker.observability.null import NullObservability
from story_maker.pipeline.acceptance import CardSync, chapter_hash
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import Production
from story_maker.pipeline.worker import Worker
from story_maker.store.models import (
    BannedTerm,
    Chapter,
    Character,
    Event,
    EventCharacter,
    Fact,
    FactUsage,
    OutlineChapter,
    Run,
)
from story_maker.store.session import unit_of_work
from story_maker.store.versions import publish

JWT_SECRET = "x" * 32
INSULT = "zoquete"
TOBY_CHAPTERS = (1, 3, 7)
CADIZ = "el viaje a Cádiz"
CADIZ_ELEMENT = 88

STARTS = ("Luego", "Después", "Allí", "Pronto", "Ayer")
_CONSONANTS = "bcdfglmnprstv"
_VOWELS = "aeiou"
# Palabras de la prueba que no pueden salir en el relleno: el «personaje desconocido» se decide
# por si la palabra aparece en algún capítulo de la vigente (019-C03).
_RESERVED = {"pepe", "nala", "tobi", "rosa", "sala", "mala"}
VOCABULARY = tuple(
    word
    for word in (
        a + b + c + d
        for a, b, c, d in itertools.product(_CONSONANTS, _VOWELS, _CONSONANTS, _VOWELS)
    )
    if word not in _RESERVED
)


def sentence(start: str, words: list[str]) -> str:
    return f"{start} {' '.join(words)}."


def clean_text(offset: int, paragraphs: int = 24, lead: str = "") -> str:
    """`paragraphs` párrafos de cinco frases de diez palabras (50 palabras cada uno), sin
    repeticiones: ningún linter avisa. `lead` abre el primer párrafo."""
    vocabulary = itertools.cycle(VOCABULARY[offset:] + VOCABULARY[:offset])
    blocks = []
    for number in range(paragraphs):
        sentences = [sentence(start, [next(vocabulary) for _ in range(9)]) for start in STARTS]
        if number == 0 and lead:
            sentences[0] = lead
        blocks.append(" ".join(sentences))
    return "\n\n".join(blocks)


def v1_text(number: int) -> str:
    """1.200 palabras. El 1, el 3 y el 7 nombran a Toby; el 1 dice «la IA»; el 2, «entonces»."""
    leads = {
        1: "Luego Marta vio a Toby junto a la IA del faro.",
        2: "Luego Marta supo entonces que el faro seguía allí.",
        3: "Luego Marta paseó con Toby por la playa del faro.",
        7: "Luego Marta llamó a Toby desde la puerta del faro.",
    }
    return clean_text(number * 200, lead=leads.get(number, ""))


@dataclass(frozen=True)
class N:
    user_a: int
    user_b: int
    novel_id: int
    v1_id: int
    marta_id: int
    toby_id: int
    toby_name: int
    cadiz: int
    rosa_id: int
    luis_id: int
    ana_id: int
    pablo_id: int


def _character(session: Session, version_id: int, name: str) -> Character:
    character = Character(
        version_id=version_id,
        type="invented",
        species="person",
        canonical_name=name,
        birth_date=None,
        origin="invented",
    )
    session.add(character)
    session.flush()
    return character


def _event(
    session: Session,
    version_id: int,
    place_id: int,
    moment: dt.datetime,
    *,
    origin: str,
    chapter: int | None,
    excluded: int | None = None,
    present: tuple[int, ...] = (),
    analepsis: bool = False,
) -> None:
    event = Event(
        version_id=version_id,
        statement=f"evento de {moment:%Y-%m}",
        moment=moment,
        place_id=place_id,
        type="exclusion" if excluded is not None else "ordinary",
        excluded_character_id=excluded,
        analepsis=analepsis,
        origin=origin,
        chapter=chapter,
        beat=1 if chapter is not None else None,
    )
    session.add(event)
    session.flush()
    for character_id in present:
        session.add(EventCharacter(event_id=event.id, character_id=character_id))


def _banned(session: Session, level: str, term: str, **owner: int) -> None:
    session.add(
        BannedTerm(
            level=level,
            term=term,
            type="word",
            keywords=None,
            normalized=normalize_token(term),
            **owner,
        )
    )


def publish_n(session_factory: sessionmaker[Session], seed: Seed) -> N:
    """La candidata de la fixture de 011 con las convenciones de 019, publicada como v1."""
    faro = seed.places["Faro de Cabo Mayor"]
    with unit_of_work(session_factory) as uow:
        session = uow.session
        version_id = seed.version_id
        seed_world(session, version_id)
        marta = session.get_one(Character, seed.characters["Marta"])
        marta.birth_date = dt.date(1990, 6, 15)
        toby = session.get_one(Character, seed.characters["Toby"])
        toby.birth_date = None
        rosa, luis, ana, pablo = (
            _character(session, version_id, name) for name in ("Rosa", "Luis", "Ana", "Pablo")
        )
        cadiz = Fact(
            version_id=version_id,
            subject_type="character",
            character_id=marta.id,
            attribute=RECOLLECTION,
            value=CADIZ,
            origin="brief",
            mandatory=True,
            personal_element_id=CADIZ_ELEMENT,
        )
        session.add(cadiz)
        outline = session.query(OutlineChapter).filter(
            OutlineChapter.version_id == version_id, OutlineChapter.number == 3
        )
        for row in outline:
            row.assigned_elements = [str(CADIZ_ELEMENT)]
        for number in range(1, 11):
            title, text = f"Capítulo {number}", v1_text(number)
            session.add(
                Chapter(
                    version_id=version_id,
                    number=number,
                    title=title,
                    text=text,
                    summary=f"Resumen {number}",
                    word_count=1200,
                    content_hash=chapter_hash(title, text),
                )
            )
        session.flush()
        for number in TOBY_CHAPTERS:
            session.add(FactUsage(fact_id=seed.facts["toby"], chapter=number))
        session.add(FactUsage(fact_id=cadiz.id, chapter=3))
        _event(
            session,
            version_id,
            faro,
            dt.datetime(2010, 5, 1),
            origin="brief",
            chapter=None,
            excluded=rosa.id,
        )
        _event(
            session,
            version_id,
            faro,
            dt.datetime(2026, 2, 10),
            origin="recorded",
            chapter=2,
            excluded=luis.id,
        )
        _event(
            session,
            version_id,
            faro,
            dt.datetime(2026, 8, 10),
            origin="recorded",
            chapter=6,
            excluded=ana.id,
        )
        _event(
            session,
            version_id,
            faro,
            dt.datetime(2026, 1, 5),
            origin="planned",
            chapter=4,
            excluded=pablo.id,
        )
        _event(
            session,
            version_id,
            faro,
            dt.datetime(2026, 3, 12, 18),
            origin="recorded",
            chapter=3,
            present=(marta.id, toby.id),
        )
        _event(
            session,
            version_id,
            faro,
            dt.datetime(2005, 7, 1),
            origin="recorded",
            chapter=8,
            present=(marta.id,),
            analepsis=True,
        )
        user_b = seed_user(session, email="b@example.com")
        _banned(session, "global", INSULT)
        _banned(session, "user", "tabaco", user_id=seed.user_id)
        _banned(session, "novel", "Jorge", novel_id=seed.novel_id)
        _banned(session, "user", "mar", user_id=user_b.id)
        session.flush()
        real_cards(uow, version_id)
        ids = N(
            user_a=seed.user_id,
            user_b=user_b.id,
            novel_id=seed.novel_id,
            v1_id=version_id,
            marta_id=marta.id,
            toby_id=toby.id,
            toby_name=seed.facts["toby"],
            cadiz=cadiz.id,
            rosa_id=rosa.id,
            luis_id=luis.id,
            ana_id=ana.id,
            pablo_id=pablo.id,
        )
    with unit_of_work(session_factory) as uow:
        publish(uow, seed.version_id, pdf_path="v1.pdf", now=NOW)
        uow.session.get_one(Run, seed.run_id).status = "published"
    return ids


@pytest.fixture
def n(session_factory: sessionmaker[Session], seed: Seed) -> N:
    return publish_n(session_factory, seed)


@pytest.fixture
def config(config: Config) -> Config:
    return dataclasses.replace(
        config, max_retries={**config.max_retries, "chapter": 3, "gate_cycles": 2}
    )


@pytest.fixture
def cards() -> CardSync:
    return real_cards


@pytest.fixture
def kit(production: Production, session_factory: sessionmaker[Session], tmp_path: Path) -> GateKit:
    return make_kit(production, session_factory, tmp_path)


@pytest.fixture
def orchestrator(production: Production, planning: PhaseDouble, kit: GateKit) -> Orchestrator:
    return Orchestrator(production=production, planning=planning, gate=kit.gate)


@pytest.fixture
def worker(production: Production, orchestrator: Orchestrator) -> Worker:
    return Worker(
        production.session_factory,
        orchestrator.execute,
        max_resumes=production.config.max_resumes,
        clock=production.clock,
    )


def headers(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id, JWT_SECRET, 24, NOW)}"}


@pytest.fixture
def client(
    session_factory: sessionmaker[Session],
    port: AgentPort,
    telemetry: NullObservability,
    config: Config,
    workspace: Path,
) -> TestClient:
    app = create_app(
        session_factory=session_factory,
        jwt_secret=JWT_SECRET,
        clock=lambda: NOW,
        agent_port=port,
        telemetry=telemetry,
        config=config,
        workspace=workspace,
    )
    return TestClient(app)


def chapter_text(session_factory: sessionmaker[Session], version_id: int, number: int) -> str:
    with session_factory() as session:
        return (
            session.query(Chapter)
            .filter(Chapter.version_id == version_id, Chapter.number == number)
            .one()
            .text
        )

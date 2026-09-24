"""Fixtures de la producción de capítulos (011): una candidata con el plan aplicado, el doble falso
del puerto de agente, el doble nulo de observabilidad y las costuras de 010, 012 y 016 dobladas.

Fixture común de la spec: `quality.thresholds` = 3, `max_retries.chapter` = 2 (como mucho 3
intentos por capítulo), `max_resumes` = 2 y un objetivo de 1.250 palabras."""

from __future__ import annotations

import dataclasses
import datetime as dt
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import Call, FakeAgent, Say, Script
from story_maker.agents.port import AgentPort
from story_maker.agents.usage import Usage
from story_maker.config import Config, load_config
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Trace
from story_maker.pipeline.acceptance import CardSync
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import ChapterProducer, Production, Prompts
from story_maker.pipeline.windows import EditorWindow, WriterWindow
from story_maker.policy.audit import record_decision
from story_maker.policy.engine import decide
from story_maker.policy.types import DecisionDePolitica, EntradaProhibida, PeticionDePolitica
from story_maker.settings import ROOT
from story_maker.store.models import (
    Brief,
    CanonCard,
    Character,
    Checkpoint,
    Event,
    EventCharacter,
    Fact,
    Novel,
    OutlineChapter,
    Place,
    Run,
    StyleSheet,
    User,
    Version,
)
from story_maker.store.session import (
    UnitOfWork,
    create_schema,
    make_engine,
    make_session_factory,
    unit_of_work,
)

NOW = dt.datetime(2026, 9, 24, 12, 0)
USAGE = Usage(input_tokens=1000, output_tokens=500, cache_read_tokens=0, cache_write_tokens=0)
BANNED = "tiburón"
CRITERIA = ("fidelidad-canon", "cumple-beats", "personalizacion-natural", "prosa", "tono")
BEATS_PER_CHAPTER = 3


def text_of(words: int, word: str = "palabra") -> str:
    """Un texto de `words` palabras en minúscula, en párrafos de 50 separados por una línea en
    blanco: no dispara `nombres-exactos`."""
    tokens = [word] * words
    paragraphs = [" ".join(tokens[i : i + 50]) for i in range(0, words, 50)]
    return "\n\n".join(paragraphs)


def chapter_call(words: int = 1250, title: str = "El faro", text: str | None = None) -> Call:
    body = text if text is not None else text_of(words)
    return Call("submit_chapter", {"title": title, "text": body})


def writer_script(*calls: Call, end: bool = True) -> Script:
    steps: tuple[Any, ...] = (*calls, Say("Fin.")) if end else calls
    return Script(steps=steps, usage=USAGE, sdk_cost_usd=0.5)


def review(
    scores: int | dict[str, int] = 4,
    *,
    defects: Sequence[dict[str, Any]] = (),
    usages: Sequence[int] = (),
    events: Sequence[dict[str, Any]] = (),
    summary: str = "Resumen del capítulo.",
) -> dict[str, Any]:
    by_criterion = dict.fromkeys(CRITERIA, scores) if isinstance(scores, int) else scores
    return {
        "scores": [
            {"criterion": c, "score": s, "justification": f"justificación de {c}"}
            for c, s in by_criterion.items()
        ],
        "defects": list(defects),
        "fact_usages": list(usages),
        "events": list(events),
        "summary": summary,
    }


def editor_script(*reviews: dict[str, Any]) -> Script:
    steps = tuple(Call("submit_review", r) for r in reviews)
    return Script(steps=(*steps, Say("Fin.")), usage=USAGE, sdk_cost_usd=0.25)


@dataclass
class Seed:
    user_id: int
    novel_id: int
    version_id: int
    run_id: int
    characters: dict[str, int]
    places: dict[str, int]
    facts: dict[str, int]


class BannedPolicy:
    """El motor de 005 con una prohibida de nivel novel y el audit log (§12.2)."""

    def __init__(self, session_factory: sessionmaker[Session], novel_id: int) -> None:
        self._session_factory = session_factory
        self.banned = [
            EntradaProhibida(term=BANNED, type="word", level="novel", owner=str(novel_id))
        ]

    def decide(self, peticion: PeticionDePolitica) -> DecisionDePolitica:
        decision = decide(peticion.model_copy(update={"banned_entries": self.banned}))
        with unit_of_work(self._session_factory) as uow:
            record_decision(uow, peticion, decision)
        return decision


@dataclass
class FixedWindows:
    """Doble de la costura de ventanas (011-C07, C08 esperan a 010 y 016)."""

    target_words: int = 1250
    residents: dict[str, Any] = field(default_factory=lambda: {"style_sheet": "tercera persona"})
    retrieved: tuple[str, ...] = ("K1", "K2")
    fail_on_chapter: int | None = None
    writer_calls: list[tuple[int, int]] = field(default_factory=list)
    editor_calls: list[tuple[int, int, str, str]] = field(default_factory=list)

    def writer(self, session: Session, version_id: int, chapter: int) -> WriterWindow:
        if chapter == self.fail_on_chapter:
            raise KeyError(f"falta el capítulo {chapter} del outline")
        self.writer_calls.append((version_id, chapter))
        return WriterWindow(
            residents={**self.residents, "chapter": chapter},
            retrieved=self.retrieved,
            target_words=self.target_words,
        )

    def editor(
        self, session: Session, version_id: int, chapter: int, title: str, text: str
    ) -> EditorWindow:
        self.editor_calls.append((version_id, chapter, title, text))
        return EditorWindow(residents={"chapter": chapter}, retrieved=("R1",))


class SuccessorCards:
    """Doble de la sincronización de 016: una sucesora con `desde_capitulo` = c+1 por cada
    personaje presente en un evento registrado del capítulo c y por cada lugar donde ocurre uno;
    las tarjetas son función de la story bible, así que lo que ya no toca se retira."""

    PREFIX = "sucesora"

    def __init__(self) -> None:
        self.calls: list[int] = []

    def __call__(self, uow: UnitOfWork, version_id: int) -> None:
        self.calls.append(version_id)
        session = uow.session
        wanted: dict[tuple[str, int | None, int | None, int], str] = {}
        recorded = session.query(Event).filter(
            Event.version_id == version_id, Event.origin == "recorded"
        )
        for event in recorded:
            assert event.chapter is not None
            since = event.chapter + 1
            present = session.query(EventCharacter).filter(EventCharacter.event_id == event.id)
            for p in present:
                key = ("character", p.character_id, None, since)
                wanted[key] = wanted.get(key, "") + event.statement
            key = ("place", None, event.place_id, since)
            wanted[key] = wanted.get(key, "") + event.statement
        existing = {
            (c.entity_type, c.character_id, c.place_id, c.from_chapter): c
            for c in session.query(CanonCard).filter(
                CanonCard.version_id == version_id, CanonCard.text.startswith(self.PREFIX)
            )
        }
        for key, card in existing.items():
            if key not in wanted or card.text != f"{self.PREFIX}: {wanted[key]}":
                uow.delete(card)
        session.flush()
        for key, statements in wanted.items():
            card = existing.get(key)
            if card is not None and card.text == f"{self.PREFIX}: {statements}":
                continue
            entity_type, character_id, place_id, since = key
            uow.add(
                CanonCard(
                    version_id=version_id,
                    entity_type=entity_type,
                    character_id=character_id,
                    place_id=place_id,
                    from_chapter=since,
                    text=f"{self.PREFIX}: {statements}",
                    content_hash=f"{key}:{statements}",
                )
            )
        session.flush()


@dataclass
class PhaseDouble:
    """Doble de una costura de fase (planificación de 010, gate de 012): registra la llamada y
    ejecuta `action` si la hay."""

    action: Callable[[int], None] | None = None
    calls: list[int] = field(default_factory=list)

    async def __call__(self, run_id: int, trace: Trace) -> None:
        self.calls.append(run_id)
        if self.action is not None:
            self.action(run_id)


@pytest.fixture
def config() -> Config:
    base = load_config(ROOT / "config.json")
    roles = dict(base.roles)
    roles["writer"] = dataclasses.replace(roles["writer"], max_turns=8)
    roles["editor"] = dataclasses.replace(roles["editor"], max_turns=8)
    return dataclasses.replace(
        base,
        max_retries={**base.max_retries, "chapter": 2},
        max_resumes=2,
        thresholds=dict.fromkeys(base.thresholds, 3),
        roles=roles,
    )


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    eng = make_engine(tmp_path / "story-maker.db")
    create_schema(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Session]:
    return make_session_factory(engine)


def seed_user(session: Session, email: str = "cliente@example.com") -> User:
    user = User(email=email, password_hash="x", created_at=NOW)
    session.add(user)
    session.flush()
    return user


def seed_novel(session: Session, user_id: int, *, confirmed: bool = True) -> Novel:
    novel = Novel(user_id=user_id, title=None, embedding_model="e5", created_at=NOW)
    session.add(novel)
    session.flush()
    session.add(Brief(novel_id=novel.id, content={}, status="confirmed" if confirmed else "draft"))
    return novel


Ids = dict[str, int]


def seed_candidate(session: Session, novel_id: int) -> tuple[Version, Ids, Ids, Ids]:
    """Una candidata con el plan aplicado: Marta y Toby, el faro, sus hechos y el outline de 10
    capítulos con 3 beats cada uno."""
    version = Version(novel_id=novel_id, status="candidate", changed_chapters=[], created_at=NOW)
    session.add(version)
    session.flush()
    marta = Character(
        version_id=version.id,
        type="recipient",
        species="person",
        canonical_name="Marta",
        birth_date=dt.date(1986, 1, 1),
        origin="brief",
    )
    toby = Character(
        version_id=version.id,
        type="close_one",
        species="animal",
        canonical_name="Toby",
        birth_date=dt.date(2021, 1, 1),
        origin="brief",
    )
    faro = Place(
        version_id=version.id, canonical_name="Faro de Cabo Mayor", description="", origin="brief"
    )
    session.add_all([marta, toby, faro])
    session.flush()
    facts = {
        "marta": Fact(
            version_id=version.id,
            subject_type="character",
            character_id=marta.id,
            attribute="name",
            value="Marta",
            origin="brief",
            mandatory=True,
        ),
        "toby": Fact(
            version_id=version.id,
            subject_type="character",
            character_id=toby.id,
            attribute="name",
            value="Toby",
            origin="brief",
            mandatory=True,
        ),
        "faro": Fact(
            version_id=version.id,
            subject_type="place",
            place_id=faro.id,
            attribute="name",
            value="Faro de Cabo Mayor",
            origin="brief",
            mandatory=False,
        ),
        "rasgo": Fact(
            version_id=version.id,
            subject_type="character",
            character_id=marta.id,
            attribute="trait",
            value="le da miedo el agua fría",
            origin="brief",
            mandatory=True,
        ),
    }
    session.add_all(facts.values())
    for number in range(1, 11):
        session.add(
            OutlineChapter(
                version_id=version.id,
                number=number,
                title=f"Capítulo {number}",
                arc_function="desarrollo",
                beats=[
                    {"number": b, "description": f"beat {b} del capítulo {number}"}
                    for b in range(1, BEATS_PER_CHAPTER + 1)
                ],
                assigned_elements=[],
            )
        )
    session.add(StyleSheet(version_id=version.id, content={"narrator": "third"}))
    session.flush()
    return (
        version,
        {"Marta": marta.id, "Toby": toby.id},
        {"Faro de Cabo Mayor": faro.id},
        {name: fact.id for name, fact in facts.items()},
    )


def seed_run(
    session: Session,
    novel_id: int,
    *,
    status: str = "running",
    phase: str | None = "writing",
    chapter: int | None = 1,
    candidate: int | None = None,
    created_at: dt.datetime = NOW,
    resumes: int = 0,
    checkpoints: Sequence[int] = (0,),
) -> Run:
    run = Run(
        novel_id=novel_id,
        type="generation",
        status=status,
        phase=phase,
        chapter=chapter,
        candidate_version_id=candidate,
        resumes=resumes,
        created_at=created_at,
    )
    session.add(run)
    session.flush()
    for k in checkpoints:
        session.add(Checkpoint(run_id=run.id, chapter=k, created_at=created_at))
    return run


@pytest.fixture
def seed(session_factory: sessionmaker[Session]) -> Seed:
    with session_factory() as session:
        user = seed_user(session)
        novel = seed_novel(session, user.id)
        version, characters, places, facts = seed_candidate(session, novel.id)
        run = seed_run(session, novel.id, candidate=version.id)
        session.commit()
        return Seed(user.id, novel.id, version.id, run.id, characters, places, facts)


@pytest.fixture
def telemetry() -> NullObservability:
    return NullObservability()


@pytest.fixture
def fake() -> FakeAgent:
    return FakeAgent()


@pytest.fixture
def ceiling(config: Config) -> TokenCeiling:
    return TokenCeiling(config.token_ceiling)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    path = tmp_path / "harness_workspace"
    path.mkdir()
    (path / "CLAUDE.md").write_text("Escribe en español.", encoding="utf-8")
    return path


@pytest.fixture
def policy(session_factory: sessionmaker[Session], seed: Seed) -> BannedPolicy:
    return BannedPolicy(session_factory, seed.novel_id)


@pytest.fixture
def port(
    fake: FakeAgent,
    config: Config,
    ceiling: TokenCeiling,
    policy: BannedPolicy,
    telemetry: NullObservability,
    session_factory: sessionmaker[Session],
    workspace: Path,
) -> AgentPort:
    return AgentPort(
        agent=fake,
        config=config,
        ceiling=ceiling,
        policy=policy,
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace,
    )


@pytest.fixture
def windows() -> FixedWindows:
    return FixedWindows()


@pytest.fixture
def cards() -> SuccessorCards:
    return SuccessorCards()


@pytest.fixture
def production(
    port: AgentPort,
    session_factory: sessionmaker[Session],
    telemetry: NullObservability,
    config: Config,
    windows: FixedWindows,
    cards: SuccessorCards,
) -> Production:
    return Production(
        port=port,
        session_factory=session_factory,
        telemetry=telemetry,
        config=config,
        windows=windows,
        cards=cards,
        clock=lambda: dt.datetime(2026, 9, 24, 13, 0, tzinfo=dt.UTC),
        prompts=Prompts(writer="Prompt del writer", editor="Prompt del editor"),
    )


@pytest.fixture
def producer(production: Production) -> ChapterProducer:
    return ChapterProducer(production)


@pytest.fixture
def planning() -> PhaseDouble:
    return PhaseDouble()


@pytest.fixture
def gate() -> PhaseDouble:
    return PhaseDouble()


@pytest.fixture
def orchestrator(production: Production, planning: PhaseDouble, gate: PhaseDouble) -> Orchestrator:
    return Orchestrator(production=production, planning=planning, gate=gate)


@pytest.fixture
def trace(telemetry: NullObservability, seed: Seed) -> Iterator[Trace]:
    with telemetry.trace(f"run:{seed.run_id}", name="generacion", session=str(seed.novel_id)) as t:
        yield t


def script_accepted_chapters(fake: FakeAgent, count: int) -> None:
    """`count` capítulos que se aceptan al primer intento."""
    for _ in range(count):
        fake.script("writer", "write", writer_script(chapter_call()))
        fake.script("editor", None, editor_script(review()))


def table_counts(session: Session, *models: type[Any]) -> dict[str, int]:
    return {m.__tablename__: session.query(m).count() for m in models}


def make_production(
    session_factory: sessionmaker[Session],
    config: Config,
    workspace: Path,
    fake: FakeAgent,
    cards: CardSync,
    novel_id: int,
) -> Production:
    """La producción de las fixtures, fuera de ellas: para las pruebas de propiedades, que
    necesitan una base nueva por ejemplo."""
    telemetry = NullObservability()
    port = AgentPort(
        agent=fake,
        config=config,
        ceiling=TokenCeiling(config.token_ceiling),
        policy=BannedPolicy(session_factory, novel_id),
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace,
    )
    return Production(
        port=port,
        session_factory=session_factory,
        telemetry=telemetry,
        config=config,
        windows=FixedWindows(),
        cards=cards,
        clock=lambda: dt.datetime(2026, 9, 24, 13, 0, tzinfo=dt.UTC),
        prompts=Prompts(writer="Prompt del writer", editor="Prompt del editor"),
    )


@contextmanager
def fresh_database(directory: Path) -> Iterator[sessionmaker[Session]]:
    engine = make_engine(directory / "story-maker.db")
    create_schema(engine)
    try:
        yield make_session_factory(engine)
    finally:
        engine.dispose()

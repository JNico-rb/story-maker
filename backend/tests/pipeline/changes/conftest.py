"""Fixtures de la ejecución de cambio (014-C12 a 014-C19): la novela de `tests/pipeline/conftest.py`
con su v1 publicada y solicitudes ya confirmadas, tal como las deja 014-C10: la `SolicitudDeCambio`
`confirmed` enlazada a una ejecución `change_request` `queued` con su versión base, sin candidata.

- v1: Marta (destinataria) y el perro Toby, el faro, sus hechos, el outline y el mundo; diez
  capítulos. «Toby» es literal en el texto de 2, 5 y 7, con `UsoDeHecho` de su nombre en 2 y 5; en
  el 9 está presente en un evento registrado, sin que se le nombre.
- Las CanonCards de v1 son las de 016 (`sync_canon_cards` con vectores fijos), y la candidata las
  sincroniza igual al aplicar el cambio y al aceptar cada capítulo.
- El gate es el de 012 con sus dobles (`tests/pipeline/gate/conftest.py`); el writer, el editor y
  el juez, el doble falso del puerto de agente."""

from __future__ import annotations

import dataclasses
import datetime as dt
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import event as sa_event
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    NOW,
    PhaseDouble,
    Seed,
    chapter_call,
    editor_script,
    review,
    text_of,
    writer_script,
)
from tests.pipeline.gate.conftest import GateKit, evaluation, judge_script, make_kit, seed_world

from story_maker.agents.fake import FakeAgent
from story_maker.config import Config
from story_maker.pipeline.acceptance import CardSync, chapter_hash
from story_maker.pipeline.changes.affected import affected_chapters
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import Production
from story_maker.pipeline.worker import Worker
from story_maker.retrieval.cards import sync_canon_cards
from story_maker.retrieval.fake import FixedVectors
from story_maker.store.models import (
    CanonCard,
    ChangeRequest,
    Chapter,
    Checkpoint,
    Event,
    EventCharacter,
    Fact,
    FactUsage,
    Run,
    Version,
)
from story_maker.store.session import UnitOfWork, unit_of_work
from story_maker.store.versions import publish

TOBY_CHAPTERS = (2, 5, 7)
TOBY_LINE = " Toby ladra a su lado."


@dataclass(frozen=True)
class V1:
    """La novela con v1 publicada: ids de la fixture de 011 más los de la versión publicada."""

    user_id: int
    novel_id: int
    v1_id: int
    toby_id: int
    marta_id: int
    faro_id: int
    toby_name: int
    trait: int


@dataclass(frozen=True)
class Confirmed:
    request_id: int
    run_id: int


def v1_text(number: int) -> str:
    return text_of(1250) + (TOBY_LINE if number in TOBY_CHAPTERS else "")


def real_cards(uow: UnitOfWork, version_id: int) -> None:
    sync_canon_cards(uow, version_id, FixedVectors())


@pytest.fixture
def config(config: Config) -> Config:
    return dataclasses.replace(config, max_retries={**config.max_retries, "gate_cycles": 2})


@pytest.fixture
def cards() -> CardSync:
    return real_cards


def publish_v1(session_factory: sessionmaker[Session], seed: Seed) -> V1:
    """La candidata de la fixture de 011 con su mundo, sus capítulos y sus CanonCards pasa a v1;
    su generación queda `published`."""
    with unit_of_work(session_factory) as uow:
        session = uow.session
        version_id = seed.version_id
        seed_world(session, version_id)
        for number in range(1, 11):
            title, text = f"Capítulo {number}", v1_text(number)
            uow.add(
                Chapter(
                    version_id=version_id,
                    number=number,
                    title=title,
                    text=text,
                    summary=f"Resumen {number}",
                    word_count=1250,
                    content_hash=chapter_hash(title, text),
                )
            )
        for number in (2, 5):
            uow.add(FactUsage(fact_id=seed.facts["toby"], chapter=number))
        event = Event(
            version_id=version_id,
            statement="el perro corre por el faro",
            moment=dt.datetime(2026, 5, 1, 10, 0),
            place_id=seed.places["Faro de Cabo Mayor"],
            type="ordinary",
            analepsis=False,
            origin="recorded",
            chapter=9,
            beat=1,
        )
        uow.add(event)
        session.flush()
        uow.add(EventCharacter(event_id=event.id, character_id=seed.characters["Toby"]))
        session.flush()
        real_cards(uow, version_id)
    with unit_of_work(session_factory) as uow:
        publish(uow, seed.version_id, pdf_path="v1.pdf", now=NOW)
        uow.session.get_one(Run, seed.run_id).status = "published"
    return V1(
        user_id=seed.user_id,
        novel_id=seed.novel_id,
        v1_id=seed.version_id,
        toby_id=seed.characters["Toby"],
        marta_id=seed.characters["Marta"],
        faro_id=seed.places["Faro de Cabo Mayor"],
        toby_name=seed.facts["toby"],
        trait=seed.facts["rasgo"],
    )


@pytest.fixture
def v1(session_factory: sessionmaker[Session], seed: Seed) -> V1:
    return publish_v1(session_factory, seed)


def change(fact_id: int, old: str, new: str) -> dict[str, Any]:
    return {
        "changes": [{"fact_id": fact_id, "old_value": old, "new_value": new}],
        "new_fact": None,
    }


def rename_toby(v1: V1) -> dict[str, Any]:
    return change(v1.toby_name, "Toby", "Nala")


def new_trait(v1: V1, value: str = "teme las tormentas") -> dict[str, Any]:
    return {
        "changes": [],
        "new_fact": {
            "subject_type": "character",
            "subject_id": v1.toby_id,
            "attribute": "trait",
            "value": value,
        },
    }


def confirm(
    session_factory: sessionmaker[Session],
    novel_id: int,
    base_id: int,
    proposal: dict[str, Any],
    *,
    created_at: dt.datetime = NOW,
    fragment_chapter: int | None = None,
) -> Confirmed:
    """Lo que deja confirmar (014-C10): la solicitud `confirmed` con su propuesta y sus afectados
    (calculados como en 014-C02), y su ejecución `change_request` `queued` con la versión base."""
    old_values = [(c["fact_id"], c["old_value"]) for c in proposal["changes"]]
    with unit_of_work(session_factory) as uow:
        affected = affected_chapters(uow.session, base_id, old_values, fragment_chapter)
        run = Run(
            novel_id=novel_id,
            type="change_request",
            status="queued",
            phase=None,
            chapter=None,
            base_version_id=base_id,
            resumes=0,
            created_at=created_at,
        )
        uow.add(run)
        uow.session.flush()
        first_fact = (proposal["changes"] or [{"fact_id": 0}])[0]["fact_id"]
        selection: dict[str, Any] = (
            {"type": "fragment", "version": 1, "chapter": fragment_chapter, "quote": "palabra"}
            if fragment_chapter is not None
            else {"type": "fact", "fact_id": first_fact}
        )
        request = ChangeRequest(
            novel_id=novel_id,
            base_version_id=base_id,
            selection_type=selection["type"],
            selection=selection,
            request="que cambie",
            proposal=proposal,
            affected_chapters=affected,
            code_hash="h",
            expires_at=created_at + dt.timedelta(minutes=15),
            status="confirmed",
            run_id=run.id,
            created_at=created_at,
        )
        uow.add(request)
        uow.session.flush()
        return Confirmed(request.id, run.id)


def script_revisions(fake: FakeAgent, count: int, *, title: str = "Revisado") -> None:
    """`count` capítulos revisados que se aceptan al primer intento."""
    for _ in range(count):
        fake.script("writer", "revise", writer_script(chapter_call(title=title)))
        fake.script("editor", None, editor_script(review()))


def script_judge(fake: FakeAgent, *evaluations: dict[str, Any]) -> None:
    for e in evaluations or (evaluation(4),):
        fake.script("judge", None, judge_script(e))


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


def run_of(session_factory: sessionmaker[Session], run_id: int) -> Run:
    with session_factory() as session:
        return session.get_one(Run, run_id)


def request_of(session_factory: sessionmaker[Session], request_id: int) -> ChangeRequest:
    with session_factory() as session:
        return session.get_one(ChangeRequest, request_id)


def versions(session_factory: sessionmaker[Session], novel_id: int) -> list[Version]:
    with session_factory() as session:
        rows = session.query(Version).filter(Version.novel_id == novel_id)
        return list(rows.order_by(Version.id).all())


def version_fingerprint(session_factory: sessionmaker[Session], version_id: int) -> Any:
    """Huella del contenido de ámbito versión: capítulos, hechos, personajes y CanonCards."""
    with session_factory() as session:
        chapters = sorted(
            (c.number, c.content_hash)
            for c in session.query(Chapter).filter(Chapter.version_id == version_id)
        )
        facts = sorted(
            (f.id, f.attribute, f.value)
            for f in session.query(Fact).filter(Fact.version_id == version_id)
        )
        cards = sorted(
            (c.id, c.content_hash)
            for c in session.query(CanonCard).filter(CanonCard.version_id == version_id)
        )
        version = session.get_one(Version, version_id)
        return (chapters, facts, cards, version.status, version.number)


def checkpoints(session_factory: sessionmaker[Session], run_id: int) -> list[int]:
    with session_factory() as session:
        rows = session.query(Checkpoint.chapter).filter(Checkpoint.run_id == run_id)
        return sorted(row[0] for row in rows.order_by(Checkpoint.id))


@contextmanager
def failing_on(model: type[Any], when: str = "before_insert") -> Iterator[None]:
    """Una caída simulada al escribir en `model`."""

    def boom(*_: Any) -> None:
        raise RuntimeError(f"fallo provocado al escribir {model.__tablename__}")

    sa_event.listen(model, when, boom)
    try:
        yield
    finally:
        sa_event.remove(model, when, boom)

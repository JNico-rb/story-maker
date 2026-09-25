"""Aceptar un capítulo es una transacción (011-C19 a 011-C23, 011-I4, 011-I11)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest
from sqlalchemy import event as sa_event
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    NOW,
    PhaseDouble,
    Seed,
    SuccessorCards,
    chapter_call,
    editor_script,
    review,
    seed_candidate,
    seed_novel,
    seed_user,
    text_of,
    writer_script,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Trace
from story_maker.pipeline.acceptance import accept_chapter, chapter_hash
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import ChapterProducer
from story_maker.pipeline.runs import RunStop
from story_maker.store.models import (
    Attempt,
    CanonCard,
    Chapter,
    Character,
    Checkpoint,
    Event,
    EventCharacter,
    Fact,
    FactUsage,
    Run,
    ValidatorResult,
    Version,
)
from story_maker.store.session import unit_of_work
from story_maker.store.version_copy import copy_version, rows_of_version
from story_maker.store.versions import publish
from story_maker.validators.chapter_rubric import ChapterReview

ACCEPTANCE_TABLES = (
    Chapter,
    FactUsage,
    Event,
    EventCharacter,
    CanonCard,
    ValidatorResult,
    Attempt,
    Checkpoint,
)


VALIDATORS = ("longitud-capitulo", "nombres-exactos", "rubrica-capitulo")


def narrated(
    seed: Seed, statement: str = "Marta sube al faro con Toby", **over: Any
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "statement": statement,
        "moment": "2026-05-01T18:00:00",
        "place_id": seed.places["Faro de Cabo Mayor"],
        "present": [
            {"character_id": seed.characters["Marta"], "age": 40},
            {"character_id": seed.characters["Toby"]},
        ],
        "type": "ordinary",
        "analepsis": False,
        "beat": 2,
    }
    base.update(over)
    return base


def full_review(seed: Seed) -> dict[str, Any]:
    return review(
        usages=[seed.facts["rasgo"]],
        events=[narrated(seed)],
        summary="Marta y Toby suben al faro.",
    )


def set_chapter(session_factory: sessionmaker[Session], run_id: int, chapter: int) -> None:
    with session_factory() as session:
        run = session.get(Run, run_id)
        assert run is not None
        run.chapter = chapter
        for k in range(1, chapter):
            session.add(Checkpoint(run_id=run_id, chapter=k, created_at=NOW))
        session.commit()


def counts(session_factory: sessionmaker[Session]) -> dict[str, int]:
    with session_factory() as session:
        return {m.__tablename__: session.query(m).count() for m in ACCEPTANCE_TABLES}


async def test_accepting_a_chapter_writes_everything_in_one_transaction(
    producer: ChapterProducer,
    fake: FakeAgent,
    cards: SuccessorCards,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    set_chapter(session_factory, seed.run_id, 4)
    text = text_of(1250)
    fake.script("writer", "write", writer_script(chapter_call(title="El faro", text=text)))
    fake.script("editor", None, editor_script(full_review(seed)))

    await producer.produce_chapter(seed.run_id, 4, trace)

    with session_factory() as session:
        chapter = session.query(Chapter).filter_by(version_id=seed.version_id, number=4).one()
        assert (chapter.title, chapter.text) == ("El faro", text)
        assert chapter.summary == "Marta y Toby suben al faro."
        assert chapter.word_count == 1250
        assert chapter.content_hash == chapter_hash("El faro", text)
        usages = session.query(FactUsage).filter_by(chapter=4).all()
        assert [u.fact_id for u in usages] == [seed.facts["rasgo"]]
        recorded = session.query(Event).filter_by(origin="recorded").one()
        assert (recorded.chapter, recorded.beat) == (4, 2)
        assert recorded.moment == dt.datetime(2026, 5, 1, 18, 0)
        presences = session.query(EventCharacter).filter_by(event_id=recorded.id)
        assert sorted((p.character_id, p.declared_age) for p in presences) == sorted(
            [(seed.characters["Marta"], 40), (seed.characters["Toby"], None)]
        )
        successors = session.query(CanonCard).filter_by(version_id=seed.version_id).all()
        assert sorted((c.entity_type, c.from_chapter) for c in successors) == [
            ("character", 5),
            ("character", 5),
            ("place", 5),
        ]
        results = session.query(ValidatorResult).filter_by(run_id=seed.run_id, chapter=4)
        assert sorted((r.validator, r.passed, r.detail["attempt"]) for r in results) == [
            ("linter-consistencia", True, 1),
            ("linter-estilo-ia", True, 1),
            ("linter-legibilidad", False, 1),
            ("linter-repeticion", False, 1),
            ("longitud-capitulo", True, 1),
            ("nombres-exactos", True, 1),
            ("rubrica-capitulo", True, 1),
        ]
        checkpoints = session.query(Checkpoint).filter_by(run_id=seed.run_id)
        assert sorted(c.chapter for c in checkpoints) == [0, 1, 2, 3, 4]
        run = session.get(Run, seed.run_id)
        assert run is not None
        assert (run.phase, run.chapter) == ("writing", 5)
    assert cards.calls == [seed.version_id]


def add_ana(session_factory: sessionmaker[Session], seed: Seed) -> int:
    with session_factory() as session:
        ana = Character(
            version_id=seed.version_id,
            type="close_one",
            species="person",
            canonical_name="Ana",
            origin="brief",
        )
        session.add(ana)
        session.flush()
        fact = Fact(
            version_id=seed.version_id,
            subject_type="character",
            character_id=ana.id,
            attribute="name",
            value="Ana",
            origin="brief",
            mandatory=False,
        )
        session.add(fact)
        session.commit()
        return fact.id


USAGE_ROWS = [
    ("el rasgo declarado", ["rasgo"], "", ["rasgo"]),
    ("«Toby,» en el texto", [], " Toby,", ["toby"]),
    ("el lugar en minúsculas", [], " el faro de cabo mayor", ["faro"]),
    ("mañana y Anabel", [], " mañana Anabel", []),
    ("declarado y en el texto", ["toby"], " Toby", ["toby"]),
    ("nada", [], "", []),
]


@pytest.mark.parametrize(("row", "declared", "extra", "expected"), USAGE_ROWS)
async def test_usages_are_the_declared_plus_the_literal_match_of_nominal_facts(
    row: str,
    declared: list[str],
    extra: str,
    expected: list[str],
    producer: ChapterProducer,
    fake: FakeAgent,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    add_ana(session_factory, seed)
    words = 1250 - len(extra.split())
    fake.script("writer", "write", writer_script(chapter_call(text=text_of(words) + extra)))
    fake.script("editor", None, editor_script(review(usages=[seed.facts[d] for d in declared])))

    await producer.produce_chapter(seed.run_id, 4, trace)

    with session_factory() as session:
        used = [u.fact_id for u in session.query(FactUsage).filter_by(chapter=4)]
    assert sorted(used) == sorted(seed.facts[e] for e in expected)


@contextmanager
def failing_on(model: type[Any], when: str = "before_insert") -> Iterator[None]:
    def boom(*_: Any) -> None:
        raise RuntimeError(f"fallo provocado al escribir {model.__tablename__}")

    sa_event.listen(model, when, boom)
    try:
        yield
    finally:
        sa_event.remove(model, when, boom)


async def test_if_the_acceptance_transaction_fails_nothing_of_the_chapter_remains(
    orchestrator: Orchestrator,
    fake: FakeAgent,
    telemetry: NullObservability,
    seed: Seed,
    session_factory: sessionmaker[Session],
) -> None:
    set_chapter(session_factory, seed.run_id, 4)
    before = counts(session_factory)
    fake.script("writer", "write", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(full_review(seed)))

    with failing_on(Checkpoint):
        await orchestrator.execute(seed.run_id)

    assert counts(session_factory) == before
    with session_factory() as session:
        run = session.get(Run, seed.run_id)
        assert run is not None
        assert (run.status, run.reason) == ("interrupted", "crash")
        candidate = session.get(Version, seed.version_id)
        assert candidate is not None
        assert candidate.status == "candidate"
    # `schema-salida` es de la tool (004) y sale durante la sesión; los del intento son los suyos.
    emitted = [s.name for s in telemetry.traces[f"run:{seed.run_id}"].scores]
    assert [n for n in emitted if n.split("/")[0] in VALIDATORS] == []


WRITES = [(m, "before_insert") for m in ACCEPTANCE_TABLES] + [(Run, "before_update")]


@pytest.mark.parametrize(("model", "when"), WRITES, ids=[f"{m.__tablename__}" for m, _ in WRITES])
async def test_the_acceptance_is_atomic_whichever_write_fails(
    model: type[Any],
    when: str,
    producer: ChapterProducer,
    fake: FakeAgent,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    set_chapter(session_factory, seed.run_id, 4)
    before = counts(session_factory)
    fake.script("writer", "write", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(full_review(seed)))

    with failing_on(model, when), pytest.raises(RunStop) as stopped:
        await producer.produce_chapter(seed.run_id, 4, trace)

    assert (stopped.value.status, stopped.value.reason) == ("interrupted", "crash")
    assert counts(session_factory) == before
    with session_factory() as session:
        run = session.get(Run, seed.run_id)
        assert run is not None
        assert run.chapter == 4


def accept(
    session_factory: sessionmaker[Session],
    cards: SuccessorCards,
    *,
    run_id: int,
    version_id: int,
    chapter: int,
    text: str,
    given: dict[str, Any],
) -> None:
    with unit_of_work(session_factory) as uow:
        accept_chapter(
            uow,
            run_id=run_id,
            version_id=version_id,
            chapter=chapter,
            title=f"Título {chapter}",
            text=text,
            word_count=1250,
            review=ChapterReview.model_validate(given),
            attempt=1,
            runs=(),
            cards=cards,
            now=NOW,
        )


def snapshot(session: Session, version_id: int) -> dict[str, list[tuple[Any, ...]]]:
    out: dict[str, list[tuple[Any, ...]]] = {}
    for model in (Chapter, FactUsage, Event, EventCharacter, CanonCard):
        rows = rows_of_version(session, model, version_id)
        columns = [c.key for c in model.__table__.columns]
        out[model.__tablename__] = [tuple(getattr(r, c) for c in columns) for r in rows]
    return out


def translated(ids: dict[str, dict[int, int]], seed: Seed) -> Seed:
    return Seed(
        seed.user_id,
        seed.novel_id,
        seed.version_id,
        seed.run_id,
        {n: ids["characters"][i] for n, i in seed.characters.items()},
        {n: ids["places"][i] for n, i in seed.places.items()},
        {n: ids["facts"][i] for n, i in seed.facts.items()},
    )


def test_re_accepting_a_chapter_replaces_what_its_previous_acceptance_left(
    cards: SuccessorCards, seed: Seed, session_factory: sessionmaker[Session]
) -> None:
    for n in range(1, 11):
        accept(
            session_factory,
            cards,
            run_id=seed.run_id,
            version_id=seed.version_id,
            chapter=n,
            text=text_of(1249) + " Toby",
            given=review(
                usages=[seed.facts["rasgo"]],
                events=[narrated(seed, f"evento del capítulo {n}", beat=1)],
            ),
        )
    with unit_of_work(session_factory) as uow:
        publish(uow, seed.version_id, pdf_path="v1.pdf", now=NOW)
        copy = copy_version(uow, seed.version_id, now=NOW)
        candidate_id = copy.version.id
        rewriting = Run(
            novel_id=seed.novel_id,
            type="change_request",
            status="running",
            phase="rewriting",
            candidate_version_id=candidate_id,
            base_version_id=seed.version_id,
            resumes=0,
            created_at=NOW,
        )
        uow.add(rewriting)
        uow.session.flush()
        rewriting_id = rewriting.id
        ids = {table: dict(mapping) for table, mapping in copy.ids.items()}
    other = translated(ids, seed)
    with session_factory() as session:
        published_before = snapshot(session, seed.version_id)
        others_before = {
            k: [r for r in rows if k != "chapters" or r[2] != 4]
            for k, rows in snapshot(session, candidate_id).items()
        }

    accept(
        session_factory,
        cards,
        run_id=rewriting_id,
        version_id=candidate_id,
        chapter=4,
        text=text_of(1250, word="nueva"),
        given=review(
            usages=[other.facts["marta"]],
            events=[
                narrated(
                    other,
                    "Marta vuelve sola al faro",
                    present=[{"character_id": other.characters["Marta"], "age": 40}],
                )
            ],
        ),
    )

    with session_factory() as session:
        chapters = session.query(Chapter).filter_by(version_id=candidate_id, number=4).all()
        assert [c.text for c in chapters] == [text_of(1250, word="nueva")]
        usages_4 = (
            session.query(FactUsage)
            .join(Fact, Fact.id == FactUsage.fact_id)
            .filter(Fact.version_id == candidate_id, FactUsage.chapter == 4)
        )
        assert sorted(u.fact_id for u in usages_4) == [other.facts["marta"]]
        events_4 = session.query(Event).filter_by(
            version_id=candidate_id, origin="recorded", chapter=4
        )
        assert [e.statement for e in events_4] == ["Marta vuelve sola al faro"]
        born_of_4 = session.query(CanonCard).filter_by(version_id=candidate_id, from_chapter=5)
        assert sorted((c.entity_type, c.text) for c in born_of_4) == [
            ("character", "sucesora: Marta vuelve sola al faro"),
            ("place", "sucesora: Marta vuelve sola al faro"),
        ]
        assert session.query(Checkpoint).filter_by(run_id=rewriting_id).count() == 0
        assert snapshot(session, seed.version_id) == published_before
        after = snapshot(session, candidate_id)
        unchanged = [r for r in after["chapters"] if r[2] != 4]
        assert unchanged == others_before["chapters"]
        other_usages = [r for r in after["fact_usages"] if r[2] != 4]
        assert other_usages == [r for r in others_before["fact_usages"] if r[2] != 4]


async def test_after_the_tenth_chapter_comes_the_gate(
    production: Any,
    planning: PhaseDouble,
    gate: PhaseDouble,
    fake: FakeAgent,
    seed: Seed,
    session_factory: sessionmaker[Session],
) -> None:
    set_chapter(session_factory, seed.run_id, 10)
    orchestrator = Orchestrator(production=production, planning=planning, gate=gate)
    fake.script("writer", "write", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(review()))

    await orchestrator.execute(seed.run_id)

    with session_factory() as session:
        run = session.get(Run, seed.run_id)
        assert run is not None
        assert (run.status, run.phase, run.chapter) == ("running", "gate", None)
        assert session.query(Checkpoint).filter_by(run_id=seed.run_id, chapter=10).count() == 1
    assert [s.request.role for s in fake.sessions] == ["writer", "editor"]
    assert gate.calls == [seed.run_id]
    assert planning.calls == []


async def test_usages_and_recorded_events_only_cite_the_candidate(
    producer: ChapterProducer,
    fake: FakeAgent,
    seed: Seed,
    trace: Trace,
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        user = seed_user(session, "otra@example.com")
        novel = seed_novel(session, user.id)
        _, their_characters, their_places, their_facts = seed_candidate(session, novel.id)
        session.commit()
    foreign = review(
        usages=[their_facts["rasgo"]],
        events=[
            narrated(
                seed,
                place_id=their_places["Faro de Cabo Mayor"],
                present=[{"character_id": their_characters["Toby"]}],
            )
        ],
    )
    fake.script("writer", "write", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(foreign, full_review(seed)))

    await producer.produce_chapter(seed.run_id, 4, trace)

    assert fake.sessions[1].reads[0].startswith("Entrada inválida para submit_review")
    with session_factory() as session:
        facts = {f.id for f in session.query(Fact).filter_by(version_id=seed.version_id)}
        characters = {c.id for c in session.query(Character).filter_by(version_id=seed.version_id)}
        usages = session.query(FactUsage).all()
        assert usages
        assert all(u.fact_id in facts for u in usages)
        recorded = session.query(Event).filter_by(origin="recorded").all()
        assert recorded
        assert all(e.version_id == seed.version_id for e in recorded)
        assert all(e.place_id in set(seed.places.values()) for e in recorded)
        presences = session.query(EventCharacter).filter(
            EventCharacter.event_id.in_([e.id for e in recorded])
        )
        assert all(p.character_id in characters for p in presences)

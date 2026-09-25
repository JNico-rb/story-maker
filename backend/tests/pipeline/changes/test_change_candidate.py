"""014-C13 · La candidata copia la base y aplica el cambio en una sola transacción."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.changes.conftest import (
    V1,
    checkpoints,
    confirm,
    failing_on,
    new_trait,
    rename_toby,
    run_of,
    script_judge,
    script_revisions,
    version_fingerprint,
    versions,
)

from story_maker.agents.fake import FakeAgent
from story_maker.pipeline.changes.run import start_change
from story_maker.pipeline.production import Production
from story_maker.pipeline.runs import resume_run
from story_maker.pipeline.worker import Worker
from story_maker.store.models import CanonCard, Character, Checkpoint, Fact, Run
from story_maker.store.session import unit_of_work
from story_maker.store.version_copy import VERSION_TABLES, rows_of_version


def _running(session_factory: sessionmaker[Session], run_id: int) -> None:
    with session_factory() as session:
        session.get_one(Run, run_id).status = "running"
        session.commit()


def _cards(session: Session, version_id: int) -> list[CanonCard]:
    return list(session.query(CanonCard).filter(CanonCard.version_id == version_id).all())


def test_the_candidate_copies_the_base_renames_the_dog_and_rebuilds_only_its_cards(
    session_factory: sessionmaker[Session], v1: V1, production: Production
) -> None:
    confirmed = confirm(session_factory, v1.novel_id, v1.v1_id, rename_toby(v1))
    _running(session_factory, confirmed.run_id)
    before = version_fingerprint(session_factory, v1.v1_id)

    start_change(production, confirmed.run_id)

    run = run_of(session_factory, confirmed.run_id)
    candidate_id = run.candidate_version_id
    assert candidate_id is not None
    assert checkpoints(session_factory, confirmed.run_id) == [0]
    with session_factory() as session:
        for model in VERSION_TABLES:
            if model is CanonCard:
                continue
            base_rows = rows_of_version(session, model, v1.v1_id)
            assert len(rows_of_version(session, model, candidate_id)) == len(base_rows)
        facts = session.query(Fact).filter(Fact.version_id == candidate_id).order_by(Fact.id)
        base_facts = session.query(Fact).filter(Fact.version_id == v1.v1_id).order_by(Fact.id)
        values = [(f.attribute, f.value) for f in facts]
        expected = [(f.attribute, "Nala" if f.id == v1.toby_name else f.value) for f in base_facts]
        assert values == expected
        names = session.query(Character.canonical_name).filter(Character.version_id == candidate_id)
        assert sorted(n for (n,) in names) == ["Marta", "Nala"]
        base_texts = [c.text for c in _cards(session, v1.v1_id)]
        texts = [c.text for c in _cards(session, candidate_id)]
        assert any("Personaje: Nala" in t for t in texts)
        assert not any("Toby" in t for t in texts)
        assert {t for t in base_texts if "Toby" not in t} <= set(texts)
        assert len(texts) == len(base_texts)
    assert version_fingerprint(session_factory, v1.v1_id) == before


def test_a_new_fact_enters_the_candidate_from_the_brief_and_not_mandatory(
    session_factory: sessionmaker[Session], v1: V1, production: Production
) -> None:
    confirmed = confirm(session_factory, v1.novel_id, v1.v1_id, new_trait(v1))
    _running(session_factory, confirmed.run_id)

    start_change(production, confirmed.run_id)

    candidate_id = run_of(session_factory, confirmed.run_id).candidate_version_id
    with session_factory() as session:
        dog = (
            session.query(Character)
            .filter(Character.version_id == candidate_id, Character.canonical_name == "Toby")
            .one()
        )
        new = session.query(Fact).filter(
            Fact.version_id == candidate_id, Fact.value == "teme las tormentas"
        )
        fact = new.one()
        assert (fact.subject_type, fact.character_id, fact.attribute) == (
            "character",
            dog.id,
            "trait",
        )
        assert (fact.origin, fact.mandatory) == ("brief", False)
        dog_cards = session.query(CanonCard).filter(
            CanonCard.version_id == candidate_id, CanonCard.character_id == dog.id
        )
        assert all("trait: teme las tormentas" in c.text for c in dog_cards)


async def test_a_crash_inside_the_transaction_leaves_nothing_and_resuming_creates_it_once(
    session_factory: sessionmaker[Session], v1: V1, fake: FakeAgent, worker: Worker
) -> None:
    confirmed = confirm(session_factory, v1.novel_id, v1.v1_id, rename_toby(v1))
    before = version_fingerprint(session_factory, v1.v1_id)

    with failing_on(Checkpoint):
        assert await worker.run_next() == confirmed.run_id

    run = run_of(session_factory, confirmed.run_id)
    assert (run.status, run.reason, run.candidate_version_id) == ("interrupted", "crash", None)
    assert [v.id for v in versions(session_factory, v1.novel_id)] == [v1.v1_id]
    assert checkpoints(session_factory, confirmed.run_id) == []
    assert version_fingerprint(session_factory, v1.v1_id) == before

    with unit_of_work(session_factory) as uow:
        resume_run(uow, confirmed.run_id)
    script_revisions(fake, 3)
    script_judge(fake)
    assert await worker.run_next() == confirmed.run_id

    assert run_of(session_factory, confirmed.run_id).status == "published"
    assert len(versions(session_factory, v1.novel_id)) == 2
    assert checkpoints(session_factory, confirmed.run_id).count(0) == 1

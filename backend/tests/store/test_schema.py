"""Esquema SQLite: creación, referencias, enumerados, solo inserción, FTS5, UoW (001-C06..C13)."""

from __future__ import annotations

import datetime as dt

import pytest
import sqlite_vec
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from story_maker.store import models
from story_maker.store.session import RejectedWrite, UnitOfWork, unit_of_work

NOW = dt.datetime(2026, 1, 1)


def make_novel(session: Session) -> models.Novel:
    user = models.User(email="a@b.com", password_hash="h", created_at=NOW)
    session.add(user)
    session.flush()
    novel = models.Novel(user_id=user.id, embedding_model="m", created_at=NOW)
    session.add(novel)
    session.flush()
    return novel


def make_version(session: Session) -> models.Version:
    novel = make_novel(session)
    version = models.Version(
        novel_id=novel.id, status="candidate", number=None, changed_chapters=[], created_at=NOW
    )
    session.add(version)
    session.flush()
    return version


# --- C6: init-db crea la base con el esquema completo -------------------------------------------


EXPECTED_TABLES = {
    "users",
    "novels",
    "banned_terms",
    "audit_log",
    "interviews",
    "interview_messages",
    "briefs",
    "free_texts",
    "extracted_facts",
    "change_requests",
    "manual_edits",
    "versions",
    "worlds",
    "characters",
    "places",
    "facts",
    "fact_usages",
    "events",
    "event_characters",
    "outline_chapters",
    "style_sheets",
    "chapters",
    "canon_cards",
    "canon_cards_fts",
    "embeddings",
    "runs",
    "attempts",
    "checkpoints",
    "role_sessions",
    "validator_results",
    "chronology_files",
}


MAPPED_MODELS = [
    cls
    for cls in models.Base.registry.mappers
    if cls.class_.__tablename__ in EXPECTED_TABLES  # type: ignore[attr-defined]
]


def test_the_schema_creates_the_31_tables_without_rows(
    engine: Engine, session_factory: sessionmaker[Session]
) -> None:
    with engine.connect() as conn:
        names = {
            row[0]
            for row in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')")
            )
        }
    assert names >= EXPECTED_TABLES

    session = session_factory()
    for mapper in MAPPED_MODELS:
        assert session.query(mapper.class_).count() == 0
    session.close()


# --- C8: toda conexión abre la base igual --------------------------------------------------------


def test_every_connection_opens_wal_foreign_keys_and_busy_timeout(engine: Engine) -> None:
    with engine.connect() as conn:
        (journal_mode,) = conn.execute(text("PRAGMA journal_mode")).fetchone()
        (foreign_keys,) = conn.execute(text("PRAGMA foreign_keys")).fetchone()
        (busy_timeout,) = conn.execute(text("PRAGMA busy_timeout")).fetchone()

    assert journal_mode == "wal"
    assert foreign_keys == 1
    assert busy_timeout == 5000


def test_the_dense_channel_is_available_on_every_connection(engine: Engine) -> None:
    with engine.connect() as conn:
        (distance_orthogonal,) = conn.execute(
            text("SELECT vec_distance_cosine(:a, :b)"),
            {
                "a": sqlite_vec.serialize_float32([1, 0]),
                "b": sqlite_vec.serialize_float32([0, 1]),
            },
        ).fetchone()
        (distance_self,) = conn.execute(
            text("SELECT vec_distance_cosine(:a, :b)"),
            {
                "a": sqlite_vec.serialize_float32([1, 0]),
                "b": sqlite_vec.serialize_float32([1, 0]),
            },
        ).fetchone()

    assert distance_orthogonal == pytest.approx(1.0)
    assert distance_self == pytest.approx(0.0)


def test_a_reader_sees_the_last_committed_state_while_a_writer_is_open(
    engine: Engine, session_factory: sessionmaker[Session]
) -> None:
    with unit_of_work(session_factory) as uow:
        make_novel(uow.session)

    write_session = session_factory()
    write_session.add(models.User(email="w@b.com", password_hash="h", created_at=NOW))
    write_session.flush()  # escritura abierta, sin commit

    read_session = session_factory()
    count = read_session.query(models.Novel).count()
    read_session.close()
    write_session.rollback()
    write_session.close()

    assert count == 1


# --- C9: ámbito y referencias obligatorias -------------------------------------------------------


def test_a_novel_without_user_id_is_rejected(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    session.add(models.Novel(embedding_model="m", created_at=NOW))  # type: ignore[call-arg]

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


def test_an_audit_log_without_user_id_is_rejected(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    session.add(
        models.AuditLog(  # type: ignore[call-arg]
            origin="policy_hook", decision="allow", rule="r", detail={}, created_at=NOW
        )
    )

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


def test_a_chapter_of_a_version_that_does_not_exist_is_rejected(
    session_factory: sessionmaker[Session],
) -> None:
    session = session_factory()
    session.add(
        models.Chapter(
            version_id=999999,
            number=1,
            title="t",
            text="x",
            summary="s",
            word_count=1,
            content_hash="h",
        )
    )

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


def test_an_attempt_with_both_run_and_change_request_is_rejected(
    session_factory: sessionmaker[Session],
) -> None:
    session = session_factory()
    novel = make_novel(session)
    run = models.Run(
        novel_id=novel.id, type="generation", status="queued", resumes=0, created_at=NOW
    )
    session.add(run)
    session.flush()
    version = models.Version(
        novel_id=novel.id, status="candidate", changed_chapters=[], created_at=NOW
    )
    session.add(version)
    session.flush()
    change_request = models.ChangeRequest(
        novel_id=novel.id,
        base_version_id=version.id,
        selection_type="fragment",
        selection={},
        request="r",
        status="proposed",
        created_at=NOW,
    )
    session.add(change_request)
    session.flush()
    session.add(
        models.Attempt(
            run_id=run.id, change_request_id=change_request.id, evaluable="chapter", number=1
        )
    )

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


def test_an_attempt_with_neither_run_nor_change_request_is_rejected(
    session_factory: sessionmaker[Session],
) -> None:
    session = session_factory()
    session.add(models.Attempt(evaluable="chapter", number=1))  # type: ignore[call-arg]

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


def test_a_role_session_without_novel_id_is_rejected(
    session_factory: sessionmaker[Session],
) -> None:
    session = session_factory()
    session.add(
        models.RoleSession(  # type: ignore[call-arg]
            role="interviewer",
            model="m",
            reserved_tokens=0,
            input_tokens=0,
            output_tokens=0,
            cache_read_tokens=0,
            cache_write_tokens=0,
            cost_usd=0,
            latency_ms=0,
            outcome="completed",
        )
    )

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


def test_a_role_session_without_run_id_is_admitted(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    novel = make_novel(session)
    session.add(
        models.RoleSession(
            novel_id=novel.id,
            role="interviewer",
            model="m",
            reserved_tokens=0,
            input_tokens=0,
            output_tokens=0,
            cache_read_tokens=0,
            cache_write_tokens=0,
            cost_usd=0,
            latency_ms=0,
            outcome="completed",
        )
    )

    session.flush()  # no lanza
    session.close()


# --- C10: enumerados, rangos, unicidades y coherencia ---------------------------------------------


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("status", "paused"),
    ],
)
def test_runs_status_rejects_a_value_outside_its_enum(
    session_factory: sessionmaker[Session], field: str, value: str
) -> None:
    session = session_factory()
    novel = make_novel(session)
    kwargs = {
        "novel_id": novel.id,
        "type": "generation",
        "status": "queued",
        "resumes": 0,
        "created_at": NOW,
    }
    kwargs[field] = value
    session.add(models.Run(**kwargs))

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


def test_audit_log_decision_block_is_rejected(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    novel = make_novel(session)
    session.add(
        models.AuditLog(
            user_id=novel.user_id,
            origin="policy_hook",
            decision="block",
            rule="r",
            detail={},
            created_at=NOW,
        )
    )

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


def test_versions_status_draft_is_rejected(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    novel = make_novel(session)
    session.add(
        models.Version(novel_id=novel.id, status="draft", changed_chapters=[], created_at=NOW)
    )

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


def test_interview_messages_author_system_is_rejected(
    session_factory: sessionmaker[Session],
) -> None:
    session = session_factory()
    novel = make_novel(session)
    interview = models.Interview(novel_id=novel.id, created_at=NOW)
    session.add(interview)
    session.flush()
    session.add(
        models.InterviewMessage(
            interview_id=interview.id, author="system", text="x", created_at=NOW
        )
    )

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


def test_role_sessions_role_narrator_is_rejected(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    novel = make_novel(session)
    session.add(
        models.RoleSession(
            novel_id=novel.id,
            role="narrator",
            model="m",
            reserved_tokens=0,
            input_tokens=0,
            output_tokens=0,
            cache_read_tokens=0,
            cache_write_tokens=0,
            cost_usd=0,
            latency_ms=0,
            outcome="completed",
        )
    )

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


@pytest.mark.parametrize("number", [0, 11])
def test_chapter_number_outside_1_to_10_is_rejected(
    session_factory: sessionmaker[Session], number: int
) -> None:
    session = session_factory()
    version = make_version(session)
    session.add(
        models.Chapter(
            version_id=version.id,
            number=number,
            title="t",
            text="x",
            summary="s",
            word_count=1,
            content_hash="h",
        )
    )

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


@pytest.mark.parametrize("number", [1, 10])
def test_chapter_number_1_and_10_are_admitted(
    session_factory: sessionmaker[Session], number: int
) -> None:
    session = session_factory()
    version = make_version(session)
    session.add(
        models.Chapter(
            version_id=version.id,
            number=number,
            title="t",
            text="x",
            summary="s",
            word_count=1,
            content_hash="h",
        )
    )

    session.flush()
    session.close()


@pytest.mark.parametrize("chapter", [-1, 11])
def test_checkpoint_outside_0_to_10_is_rejected(
    session_factory: sessionmaker[Session], chapter: int
) -> None:
    session = session_factory()
    novel = make_novel(session)
    run = models.Run(
        novel_id=novel.id, type="generation", status="queued", resumes=0, created_at=NOW
    )
    session.add(run)
    session.flush()
    session.add(models.Checkpoint(run_id=run.id, chapter=chapter, created_at=NOW))

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


@pytest.mark.parametrize("chapter", [0, 10])
def test_checkpoint_0_and_10_are_admitted(
    session_factory: sessionmaker[Session], chapter: int
) -> None:
    session = session_factory()
    novel = make_novel(session)
    run = models.Run(
        novel_id=novel.id, type="generation", status="queued", resumes=0, created_at=NOW
    )
    session.add(run)
    session.flush()
    session.add(models.Checkpoint(run_id=run.id, chapter=chapter, created_at=NOW))

    session.flush()
    session.close()


@pytest.mark.parametrize(
    ("field", "value"),
    [("from_chapter", 0)],
)
def test_canon_card_from_chapter_0_is_rejected(
    session_factory: sessionmaker[Session], field: str, value: int
) -> None:
    session = session_factory()
    version = make_version(session)
    world = models.World(
        version_id=version.id,
        novum_description="d",
        novum_scope="technological",
        novum_date=dt.date(2026, 1, 1),
        consequences=[],
    )
    session.add(world)
    session.flush()
    session.add(
        models.CanonCard(
            version_id=version.id,
            entity_type="world",
            from_chapter=value,
            text="t",
            content_hash="h",
        )
    )

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


def test_attempts_number_0_is_rejected(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    novel = make_novel(session)
    run = models.Run(
        novel_id=novel.id, type="generation", status="queued", resumes=0, created_at=NOW
    )
    session.add(run)
    session.flush()
    session.add(models.Attempt(run_id=run.id, evaluable="chapter", number=0))

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


def test_runs_resumes_negative_is_rejected(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    novel = make_novel(session)
    session.add(
        models.Run(
            novel_id=novel.id, type="generation", status="queued", resumes=-1, created_at=NOW
        )
    )

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


def test_a_second_user_with_the_same_email_is_rejected(
    session_factory: sessionmaker[Session],
) -> None:
    session = session_factory()
    session.add(models.User(email="dup@b.com", password_hash="h", created_at=NOW))
    session.flush()
    session.add(models.User(email="dup@b.com", password_hash="h2", created_at=NOW))

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


def test_several_candidate_versions_without_a_number_are_admitted(
    session_factory: sessionmaker[Session],
) -> None:
    session = session_factory()
    novel = make_novel(session)
    session.add(
        models.Version(novel_id=novel.id, status="candidate", changed_chapters=[], created_at=NOW)
    )
    session.add(
        models.Version(novel_id=novel.id, status="candidate", changed_chapters=[], created_at=NOW)
    )

    session.flush()  # no lanza
    session.close()


def test_published_without_a_number_is_rejected(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    novel = make_novel(session)
    session.add(
        models.Version(
            novel_id=novel.id,
            status="published",
            changed_chapters=[],
            created_at=NOW,
            published_at=NOW,
        )
    )

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


def test_candidate_with_a_number_is_rejected(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    novel = make_novel(session)
    session.add(
        models.Version(
            novel_id=novel.id, status="candidate", number=1, changed_chapters=[], created_at=NOW
        )
    )

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


def test_published_with_number_and_date_is_admitted(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    novel = make_novel(session)
    session.add(
        models.Version(
            novel_id=novel.id,
            status="published",
            number=1,
            changed_chapters=[],
            created_at=NOW,
            published_at=NOW,
        )
    )

    session.flush()
    session.close()


def test_banned_terms_user_without_user_id_is_rejected(
    session_factory: sessionmaker[Session],
) -> None:
    session = session_factory()
    session.add(models.BannedTerm(level="user", term="x", type="word", normalized="x"))  # type: ignore[call-arg]

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


def test_banned_terms_well_formed_at_each_level_are_admitted(
    session_factory: sessionmaker[Session],
) -> None:
    session = session_factory()
    novel = make_novel(session)
    session.add(models.BannedTerm(level="global", term="a", type="word", normalized="a"))
    session.add(
        models.BannedTerm(
            level="user", user_id=novel.user_id, term="b", type="word", normalized="b"
        )
    )
    session.add(
        models.BannedTerm(level="novel", novel_id=novel.id, term="c", type="word", normalized="c")
    )

    session.flush()
    session.close()


def test_facts_character_without_character_id_is_rejected(
    session_factory: sessionmaker[Session],
) -> None:
    session = session_factory()
    version = make_version(session)
    session.add(
        models.Fact(
            version_id=version.id,
            subject_type="character",
            attribute="a",
            value="v",
            origin="brief",
            mandatory=False,
        )
    )

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


def test_events_exclusion_without_excluded_character_is_rejected(
    session_factory: sessionmaker[Session],
) -> None:
    session = session_factory()
    version = make_version(session)
    place = models.Place(
        version_id=version.id, canonical_name="p", description="d", origin="invented"
    )
    session.add(place)
    session.flush()
    session.add(
        models.Event(
            version_id=version.id,
            statement="s",
            moment=dt.date(2026, 1, 1),
            place_id=place.id,
            type="exclusion",
            analepsis=False,
            origin="planned",
        )
    )

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


def test_an_event_moment_keeps_its_date_hour_and_minute(
    session_factory: sessionmaker[Session],
) -> None:
    """El momento de un Evento es fecha y hora (`definitions.md` §2 Evento): T1, T3, T4 y T5
    comparan hasta el minuto (hallazgo de la 007, corregido en la 009)."""
    session = session_factory()
    version = make_version(session)
    place = models.Place(version_id=version.id, canonical_name="p", description="", origin="brief")
    session.add(place)
    session.flush()
    event = models.Event(
        version_id=version.id,
        statement="s",
        moment=dt.datetime(2026, 5, 10, 18, 30),
        place_id=place.id,
        type="ordinary",
        analepsis=False,
        origin="recorded",
        chapter=1,
        beat=2,
    )
    session.add(event)
    session.commit()
    event_id = event.id
    session.close()

    reread = session_factory()
    stored = reread.get(models.Event, event_id)
    assert stored is not None
    assert stored.moment == dt.datetime(2026, 5, 10, 18, 30)
    reread.close()


def test_runs_reason_stale_is_rejected(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    novel = make_novel(session)
    session.add(
        models.Run(
            novel_id=novel.id,
            type="generation",
            status="failed",
            resumes=0,
            reason="stale",
            created_at=NOW,
        )
    )

    with pytest.raises(IntegrityError):
        session.flush()
    session.close()


@pytest.mark.parametrize("reason", ["stale_base", "crash"])
def test_runs_reason_stale_base_and_crash_are_admitted(
    session_factory: sessionmaker[Session], reason: str
) -> None:
    session = session_factory()
    novel = make_novel(session)
    session.add(
        models.Run(
            novel_id=novel.id,
            type="generation",
            status="failed",
            resumes=0,
            reason=reason,
            created_at=NOW,
        )
    )

    session.flush()
    session.close()


# --- C11: solo inserción y CanonCards inmutables --------------------------------------------------


@pytest.mark.parametrize("model_name", ["AuditLog", "Checkpoint", "Embedding"])
def test_modifying_an_insert_only_row_is_rejected(
    session_factory: sessionmaker[Session], model_name: str
) -> None:
    session = session_factory()
    novel = make_novel(session)
    if model_name == "AuditLog":
        row: object = models.AuditLog(
            user_id=novel.user_id,
            origin="policy_hook",
            decision="allow",
            rule="r",
            detail={},
            created_at=NOW,
        )
    elif model_name == "Checkpoint":
        run = models.Run(
            novel_id=novel.id, type="generation", status="queued", resumes=0, created_at=NOW
        )
        session.add(run)
        session.flush()
        row = models.Checkpoint(run_id=run.id, chapter=0, created_at=NOW)
    else:
        row = models.Embedding(content_hash="h", model="m", vector=b"\x00")
    session.add(row)
    session.commit()

    uow = UnitOfWork(session)
    if model_name == "AuditLog":
        row.detail = {"x": 1}  # type: ignore[attr-defined]
    elif model_name == "Checkpoint":
        row.chapter = 5  # type: ignore[attr-defined]
    else:
        row.model = "changed"  # type: ignore[attr-defined]

    with pytest.raises(RejectedWrite):
        uow.commit()
    session.rollback()
    session.close()


def test_deleting_an_insert_only_row_is_rejected(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    embedding = models.Embedding(content_hash="h", model="m", vector=b"\x00")
    session.add(embedding)
    session.commit()

    uow = UnitOfWork(session)
    with pytest.raises(RejectedWrite):
        uow.delete(embedding)
    session.rollback()
    session.close()


def test_inserting_into_insert_only_tables_is_admitted(
    session_factory: sessionmaker[Session],
) -> None:
    session = session_factory()
    uow = UnitOfWork(session)
    uow.add(models.Embedding(content_hash="h2", model="m", vector=b"\x00"))
    uow.commit()
    session.close()


def test_modifying_a_canon_card_is_rejected(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    version = make_version(session)
    world = models.World(
        version_id=version.id,
        novum_description="d",
        novum_scope="technological",
        novum_date=dt.date(2026, 1, 1),
        consequences=[],
    )
    session.add(world)
    session.flush()
    card = models.CanonCard(
        version_id=version.id,
        entity_type="world",
        from_chapter=1,
        text="La canción de Toby",
        content_hash="h",
    )
    session.add(card)
    session.commit()

    uow = UnitOfWork(session)
    card.text = "otro texto"

    with pytest.raises(RejectedWrite):
        uow.commit()
    session.rollback()
    session.close()


def test_deleting_a_canon_card_is_admitted(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    version = make_version(session)
    world = models.World(
        version_id=version.id,
        novum_description="d",
        novum_scope="technological",
        novum_date=dt.date(2026, 1, 1),
        consequences=[],
    )
    session.add(world)
    session.flush()
    card = models.CanonCard(
        version_id=version.id, entity_type="world", from_chapter=1, text="tarjeta", content_hash="h"
    )
    uow = UnitOfWork(session)
    uow.add(card)
    uow.commit()

    uow = UnitOfWork(session)
    uow.delete(card)
    uow.commit()

    remaining = session.query(models.CanonCard).count()
    session.close()
    assert remaining == 0


# --- C12: el índice FTS5 sigue a las CanonCards, sin acentos --------------------------------------


def _search(session: Session, term: str) -> list[int]:
    rows = session.execute(
        text("SELECT rowid FROM canon_cards_fts WHERE canon_cards_fts MATCH :q"), {"q": term}
    ).fetchall()
    return [row[0] for row in rows]


@pytest.mark.parametrize("term", ["cancion", "Canción", "CANCION"])
def test_a_card_is_found_accent_insensitive(
    session_factory: sessionmaker[Session], term: str
) -> None:
    session = session_factory()
    version = make_version(session)
    world = models.World(
        version_id=version.id,
        novum_description="d",
        novum_scope="technological",
        novum_date=dt.date(2026, 1, 1),
        consequences=[],
    )
    session.add(world)
    session.flush()
    card = models.CanonCard(
        version_id=version.id,
        entity_type="world",
        from_chapter=1,
        text="La canción de Toby",
        content_hash="h",
    )
    uow = UnitOfWork(session)
    uow.add(card)
    uow.commit()

    found = _search(session, term)
    session.close()
    assert card.id in found


def test_deleting_a_card_removes_it_from_the_index(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    version = make_version(session)
    world = models.World(
        version_id=version.id,
        novum_description="d",
        novum_scope="technological",
        novum_date=dt.date(2026, 1, 1),
        consequences=[],
    )
    session.add(world)
    session.flush()
    card = models.CanonCard(
        version_id=version.id, entity_type="world", from_chapter=1, text="cancion", content_hash="h"
    )
    uow = UnitOfWork(session)
    uow.add(card)
    uow.commit()
    card_id = card.id

    uow = UnitOfWork(session)
    uow.delete(card)
    uow.commit()

    found = _search(session, "cancion")
    session.close()
    assert card_id not in found


def test_a_rolled_back_transaction_leaves_neither_the_card_nor_its_index_entry(
    session_factory: sessionmaker[Session],
) -> None:
    session = session_factory()
    version = make_version(session)
    world = models.World(
        version_id=version.id,
        novum_description="d",
        novum_scope="technological",
        novum_date=dt.date(2026, 1, 1),
        consequences=[],
    )
    session.add(world)
    session.flush()
    uow = UnitOfWork(session)
    uow.add(
        models.CanonCard(
            version_id=version.id,
            entity_type="world",
            from_chapter=1,
            text="cancion",
            content_hash="h",
        )
    )
    uow.rollback()

    cards = session.query(models.CanonCard).count()
    found = _search(session, "cancion")
    session.close()
    assert cards == 0
    assert found == []


# --- C13: una unidad de trabajo es todo o nada ----------------------------------------------------


def _insert_two_rows_and_fail(session: Session) -> None:
    with UnitOfWork(session) as uow:
        user = models.User(email="uow@b.com", password_hash="h", created_at=NOW)
        uow.add(user)
        session.flush()
        uow.add(models.Novel(user_id=user.id, embedding_model="m", created_at=NOW))
        raise RuntimeError("fallo antes de confirmar")


def test_a_failed_unit_of_work_leaves_no_row(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    with pytest.raises(RuntimeError):
        _insert_two_rows_and_fail(session)

    users = session.query(models.User).filter_by(email="uow@b.com").count()
    novels = session.query(models.Novel).count()
    session.close()
    assert users == 0
    assert novels == 0


def test_a_unit_of_work_without_failure_keeps_both_rows(
    session_factory: sessionmaker[Session],
) -> None:
    session = session_factory()
    with UnitOfWork(session) as uow:
        user = models.User(email="uow2@b.com", password_hash="h", created_at=NOW)
        uow.add(user)
        session.flush()
        uow.add(models.Novel(user_id=user.id, embedding_model="m", created_at=NOW))

    users = session.query(models.User).filter_by(email="uow2@b.com").count()
    novels = session.query(models.Novel).count()
    session.close()
    assert users == 1
    assert novels == 1

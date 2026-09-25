"""Esquema SQLite completo: 31 tablas (`architecture.md` §15.6, detalle de columna de la 001)."""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import JSON, CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from story_maker.domain.constants import CHAPTERS_PER_NOVEL, ROLES

CHAPTER_RANGE = f"BETWEEN 1 AND {CHAPTERS_PER_NOVEL}"
CHECKPOINT_RANGE = f"BETWEEN 0 AND {CHAPTERS_PER_NOVEL}"
ROLE_LIST = ", ".join(f"'{role}'" for role in ROLES)


class Base(DeclarativeBase):
    pass


def _enum_check(column: str, values: tuple[str, ...]) -> CheckConstraint:
    listed = ", ".join(f"'{v}'" for v in values)
    return CheckConstraint(f"{column} IN ({listed})", name=f"ck_{column}_enum")


# --- Cuentas, entrada y peticiones ------------------------------------------------------------


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    created_at: Mapped[dt.datetime]


class Novel(Base):
    __tablename__ = "novels"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str | None]
    embedding_model: Mapped[str]
    created_at: Mapped[dt.datetime]
    # El slug del brief de `ejemplos/briefs/` del que sale (020: `evals run`, `example`).
    eval_brief: Mapped[str | None]


class BannedTerm(Base):
    __tablename__ = "banned_terms"
    __table_args__ = (
        _enum_check("level", ("global", "user", "novel")),
        _enum_check("type", ("word", "topic")),
        CheckConstraint(
            "(level = 'global' AND user_id IS NULL AND novel_id IS NULL) OR "
            "(level = 'user' AND user_id IS NOT NULL AND novel_id IS NULL) OR "
            "(level = 'novel' AND novel_id IS NOT NULL AND user_id IS NULL)",
            name="ck_banned_terms_scope",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    level: Mapped[str]
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    novel_id: Mapped[int | None] = mapped_column(ForeignKey("novels.id"))
    term: Mapped[str]
    type: Mapped[str]
    keywords: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSON)
    normalized: Mapped[str]


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        _enum_check(
            "origin",
            (
                "policy_hook",
                "free_text",
                "change_request",
                "manual_edit",
                "publication_gate",
                "mcp_write",
            ),
        ),
        _enum_check("decision", ("allow", "deny", "flag")),
        _enum_check("role", ROLES),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    novel_id: Mapped[int | None] = mapped_column(ForeignKey("novels.id"))
    run_id: Mapped[int | None] = mapped_column(ForeignKey("runs.id"))
    role: Mapped[str | None]
    tool: Mapped[str | None]
    origin: Mapped[str]
    decision: Mapped[str]
    rule: Mapped[str]
    detail: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSON)
    created_at: Mapped[dt.datetime]


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id"), unique=True)
    created_at: Mapped[dt.datetime]


class InterviewMessage(Base):
    __tablename__ = "interview_messages"
    __table_args__ = (_enum_check("author", ("user", "interviewer")),)

    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"))
    author: Mapped[str]
    text: Mapped[str]
    created_at: Mapped[dt.datetime]


class Brief(Base):
    __tablename__ = "briefs"
    __table_args__ = (_enum_check("status", ("draft", "confirmed")),)

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id"), unique=True)
    content: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSON)
    status: Mapped[str]


class FreeText(Base):
    __tablename__ = "free_texts"

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id"))
    content: Mapped[str]
    discarded_instructions: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSON)
    created_at: Mapped[dt.datetime]


class ExtractedFact(Base):
    __tablename__ = "extracted_facts"

    id: Mapped[int] = mapped_column(primary_key=True)
    free_text_id: Mapped[int] = mapped_column(ForeignKey("free_texts.id"))
    subject: Mapped[str]
    attribute: Mapped[str]
    value: Mapped[str]
    quote: Mapped[str]
    verified: Mapped[bool]
    accepted: Mapped[bool | None]
    mandatory: Mapped[bool]


class ChangeRequest(Base):
    __tablename__ = "change_requests"
    __table_args__ = (
        _enum_check("selection_type", ("fragment", "fact")),
        _enum_check("status", ("proposed", "confirmed", "applied", "rejected", "expired")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id"))
    base_version_id: Mapped[int] = mapped_column(ForeignKey("versions.id"))
    selection_type: Mapped[str]
    selection: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSON)
    request: Mapped[str]
    proposal: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSON)
    affected_chapters: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSON)
    code_hash: Mapped[str | None]
    expires_at: Mapped[dt.datetime | None]
    status: Mapped[str]
    run_id: Mapped[int | None] = mapped_column(ForeignKey("runs.id"), unique=True)
    created_at: Mapped[dt.datetime]


class ManualEdit(Base):
    __tablename__ = "manual_edits"
    __table_args__ = (
        CheckConstraint(f"chapter {CHAPTER_RANGE}", name="ck_manual_edits_chapter_range"),
        _enum_check("status", ("queued", "applied", "rejected")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id"))
    base_version_id: Mapped[int] = mapped_column(ForeignKey("versions.id"))
    chapter: Mapped[int]
    text: Mapped[str]
    status: Mapped[str]
    run_id: Mapped[int | None] = mapped_column(ForeignKey("runs.id"), unique=True)
    created_at: Mapped[dt.datetime]


# --- Una versión: story bible, artefacto e índice ---------------------------------------------


class Version(Base):
    __tablename__ = "versions"
    __table_args__ = (
        _enum_check("status", ("candidate", "published", "discarded")),
        UniqueConstraint("novel_id", "number"),
        CheckConstraint(
            "(status = 'published' AND number IS NOT NULL AND published_at IS NOT NULL) OR "
            "(status != 'published' AND number IS NULL AND published_at IS NULL)",
            name="ck_versions_published_fields",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id"))
    status: Mapped[str]
    number: Mapped[int | None]
    base_version_id: Mapped[int | None] = mapped_column(ForeignKey("versions.id"))
    changed_chapters: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSON)
    pdf_path: Mapped[str | None]
    created_at: Mapped[dt.datetime]
    published_at: Mapped[dt.datetime | None]


class World(Base):
    __tablename__ = "worlds"
    __table_args__ = (_enum_check("novum_scope", ("technological", "social", "cognitive")),)

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("versions.id"), unique=True)
    novum_description: Mapped[str]
    novum_scope: Mapped[str]
    novum_date: Mapped[dt.date]
    consequences: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSON)


class Character(Base):
    __tablename__ = "characters"
    __table_args__ = (
        _enum_check("type", ("recipient", "close_one", "invented")),
        _enum_check("species", ("person", "animal", "artificial")),
        _enum_check("origin", ("brief", "invented")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("versions.id"))
    type: Mapped[str]
    species: Mapped[str]
    canonical_name: Mapped[str]
    birth_date: Mapped[dt.date | None]
    origin: Mapped[str]


class Place(Base):
    __tablename__ = "places"
    __table_args__ = (_enum_check("origin", ("brief", "invented")),)

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("versions.id"))
    canonical_name: Mapped[str]
    description: Mapped[str]
    origin: Mapped[str]


class Fact(Base):
    __tablename__ = "facts"
    __table_args__ = (
        _enum_check("subject_type", ("character", "place", "world")),
        _enum_check("origin", ("brief", "free_text", "invented")),
        CheckConstraint(
            "(subject_type = 'character' AND character_id IS NOT NULL AND place_id IS NULL) OR "
            "(subject_type = 'place' AND place_id IS NOT NULL AND character_id IS NULL) OR "
            "(subject_type = 'world' AND character_id IS NULL AND place_id IS NULL)",
            name="ck_facts_subject",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("versions.id"))
    subject_type: Mapped[str]
    character_id: Mapped[int | None] = mapped_column(ForeignKey("characters.id"))
    place_id: Mapped[int | None] = mapped_column(ForeignKey("places.id"))
    attribute: Mapped[str]
    value: Mapped[str]
    origin: Mapped[str]
    mandatory: Mapped[bool]
    personal_element_id: Mapped[int | None]


class FactUsage(Base):
    __tablename__ = "fact_usages"
    __table_args__ = (
        CheckConstraint(f"chapter {CHAPTER_RANGE}", name="ck_fact_usages_chapter_range"),
        UniqueConstraint("fact_id", "chapter"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    fact_id: Mapped[int] = mapped_column(ForeignKey("facts.id"))
    chapter: Mapped[int]


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(
            f"chapter IS NULL OR chapter {CHAPTER_RANGE}", name="ck_events_chapter_range"
        ),
        _enum_check("type", ("ordinary", "exclusion")),
        _enum_check("origin", ("brief", "planned", "recorded")),
        CheckConstraint(
            "(type = 'exclusion' AND excluded_character_id IS NOT NULL) OR "
            "(type = 'ordinary' AND excluded_character_id IS NULL)",
            name="ck_events_exclusion",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("versions.id"))
    statement: Mapped[str]
    moment: Mapped[dt.datetime]  # fecha y hora (`definitions.md` §2 Evento)
    place_id: Mapped[int] = mapped_column(ForeignKey("places.id"))
    type: Mapped[str]
    excluded_character_id: Mapped[int | None] = mapped_column(ForeignKey("characters.id"))
    analepsis: Mapped[bool]
    origin: Mapped[str]
    chapter: Mapped[int | None]
    beat: Mapped[int | None]


class EventCharacter(Base):
    __tablename__ = "event_characters"
    __table_args__ = (UniqueConstraint("event_id", "character_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"))
    declared_age: Mapped[int | None]


class OutlineChapter(Base):
    __tablename__ = "outline_chapters"
    __table_args__ = (
        CheckConstraint(f"number {CHAPTER_RANGE}", name="ck_outline_chapters_number_range"),
        UniqueConstraint("version_id", "number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("versions.id"))
    number: Mapped[int]
    title: Mapped[str]
    arc_function: Mapped[str]
    beats: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSON)
    assigned_elements: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSON)


class StyleSheet(Base):
    __tablename__ = "style_sheets"

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("versions.id"), unique=True)
    content: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSON)


class Chapter(Base):
    __tablename__ = "chapters"
    __table_args__ = (
        CheckConstraint(f"number {CHAPTER_RANGE}", name="ck_chapters_number_range"),
        UniqueConstraint("version_id", "number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("versions.id"))
    number: Mapped[int]
    title: Mapped[str]
    text: Mapped[str]
    summary: Mapped[str]
    word_count: Mapped[int]
    content_hash: Mapped[str]


class CanonCard(Base):
    __tablename__ = "canon_cards"
    __table_args__ = (
        _enum_check("entity_type", ("character", "place", "world")),
        CheckConstraint("from_chapter >= 1", name="ck_canon_cards_from_chapter"),
        CheckConstraint(
            "(entity_type = 'character' AND character_id IS NOT NULL AND place_id IS NULL) OR "
            "(entity_type = 'place' AND place_id IS NOT NULL AND character_id IS NULL) OR "
            "(entity_type = 'world' AND character_id IS NULL AND place_id IS NULL)",
            name="ck_canon_cards_entity",
        ),
        UniqueConstraint("version_id", "entity_type", "character_id", "place_id", "from_chapter"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("versions.id"))
    entity_type: Mapped[str]
    character_id: Mapped[int | None] = mapped_column(ForeignKey("characters.id"))
    place_id: Mapped[int | None] = mapped_column(ForeignKey("places.id"))
    from_chapter: Mapped[int]
    text: Mapped[str]
    content_hash: Mapped[str]


class Embedding(Base):
    __tablename__ = "embeddings"
    __table_args__ = (UniqueConstraint("content_hash", "model"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    content_hash: Mapped[str]
    model: Mapped[str]
    vector: Mapped[bytes]


# --- Ejecuciones y calidad ----------------------------------------------------------------------


class Run(Base):
    __tablename__ = "runs"
    __table_args__ = (
        CheckConstraint(
            f"chapter IS NULL OR chapter {CHAPTER_RANGE}", name="ck_runs_chapter_range"
        ),
        CheckConstraint("resumes >= 0", name="ck_runs_resumes"),
        _enum_check("type", ("generation", "change_request", "manual_edit")),
        _enum_check("status", ("queued", "running", "published", "failed", "interrupted")),
        CheckConstraint(
            "phase IS NULL OR phase IN ('planning', 'writing', 'gate', 'rewriting')",
            name="ck_runs_phase",
        ),
        CheckConstraint(
            "reason IS NULL OR reason IN ("
            "'retries_exhausted', 'banned_content', 'render_failure', 'unattributable_defect', "
            "'edit_rejected', 'infeasible_config', 'internal_error', 'stale_base', "
            "'resumes_exhausted', 'crash', 'provider_error', 'verifier_unreachable', "
            "'verifier_timeout')",
            name="ck_runs_reason",
        ),
        UniqueConstraint("candidate_version_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id"))
    type: Mapped[str]
    status: Mapped[str]
    phase: Mapped[str | None]
    chapter: Mapped[int | None]
    base_version_id: Mapped[int | None] = mapped_column(ForeignKey("versions.id"))
    candidate_version_id: Mapped[int | None] = mapped_column(ForeignKey("versions.id"))
    resumes: Mapped[int]
    reason: Mapped[str | None]
    reason_detail: Mapped[str | None]
    created_at: Mapped[dt.datetime]
    finished_at: Mapped[dt.datetime | None]


class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (
        CheckConstraint(
            f"chapter IS NULL OR chapter {CHAPTER_RANGE}", name="ck_attempts_chapter_range"
        ),
        CheckConstraint("number >= 1", name="ck_attempts_number"),
        _enum_check("evaluable", ("chapter", "plan", "gate_cycle", "change")),
        CheckConstraint(
            "outcome IS NULL OR outcome IN ('accept', 'rewrite', 'fail')",
            name="ck_attempts_outcome",
        ),
        CheckConstraint(
            "(run_id IS NOT NULL AND change_request_id IS NULL) OR "
            "(run_id IS NULL AND change_request_id IS NOT NULL)",
            name="ck_attempts_owner",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("runs.id"))
    change_request_id: Mapped[int | None] = mapped_column(ForeignKey("change_requests.id"))
    evaluable: Mapped[str]
    chapter: Mapped[int | None]
    gate_cycle: Mapped[int | None]
    number: Mapped[int]
    outcome: Mapped[str | None]


class Checkpoint(Base):
    __tablename__ = "checkpoints"
    __table_args__ = (
        CheckConstraint(f"chapter {CHECKPOINT_RANGE}", name="ck_checkpoints_chapter_range"),
        UniqueConstraint("run_id", "chapter"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    chapter: Mapped[int]
    created_at: Mapped[dt.datetime]


class RoleSession(Base):
    __tablename__ = "role_sessions"
    __table_args__ = (
        CheckConstraint(
            f"chapter IS NULL OR chapter {CHAPTER_RANGE}", name="ck_role_sessions_chapter_range"
        ),
        _enum_check("role", ROLES),
        _enum_check(
            "outcome",
            ("completed", "turns_exhausted", "time_exhausted", "cut", "infrastructure_failure"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id"))
    run_id: Mapped[int | None] = mapped_column(ForeignKey("runs.id"))
    role: Mapped[str]
    chapter: Mapped[int | None]
    model: Mapped[str]
    prompt_version: Mapped[str | None]
    reserved_tokens: Mapped[int]
    # Uso y coste vacíos, nunca a cero, si la sesión cierra sin resultado final (§18).
    input_tokens: Mapped[int | None]
    output_tokens: Mapped[int | None]
    cache_read_tokens: Mapped[int | None]
    cache_write_tokens: Mapped[int | None]
    cost_usd: Mapped[float | None]
    sdk_cost_usd: Mapped[float | None]
    latency_ms: Mapped[int]
    outcome: Mapped[str]
    trace_id: Mapped[str | None]


class ValidatorResult(Base):
    __tablename__ = "validator_results"
    __table_args__ = (
        CheckConstraint(
            f"chapter IS NULL OR chapter {CHAPTER_RANGE}", name="ck_validator_results_chapter_range"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    version_id: Mapped[int] = mapped_column(ForeignKey("versions.id"))
    validator: Mapped[str]
    chapter: Mapped[int | None]
    passed: Mapped[bool]
    score: Mapped[float | None]
    detail: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSON)
    created_at: Mapped[dt.datetime]


class ChronologyFile(Base):
    __tablename__ = "chronology_files"
    __table_args__ = (_enum_check("result", ("passed", "failed", "error")),)

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    content_hash: Mapped[str]
    result: Mapped[str]
    detail: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSON)
    created_at: Mapped[dt.datetime]


INSERT_ONLY_TABLES = (AuditLog, Checkpoint, Embedding)

# `canon_cards_fts`: índice FTS5 sin modelo ORM, creado y sincronizado a mano (§15.9, C11-C13).
CANON_CARDS_FTS_DDL = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS canon_cards_fts USING fts5("
    "text, content='canon_cards', content_rowid='id', "
    "tokenize='unicode61 remove_diacritics 2')"
)

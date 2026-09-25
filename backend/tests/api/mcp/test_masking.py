"""015-C17: las trazas pasan por la máscara y nunca llevan el código de confirmación ni el PDF.

A tiene dos novelas con destinatarios distintos, con nombres ficticios (y su fecha de
nacimiento). El doble nulo captura lo que se exportaría a Langfuse; nada de eso debe llevar esos
nombres o esa fecha (`architecture.md` §13.5), ni el código de confirmación (015-I9), ni los
bytes del PDF (`verification.md` §5, fila 015-I10)."""

from __future__ import annotations

import base64
import dataclasses
import datetime as dt
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from tests.api.mcp.conftest import owner_headers

from story_maker.agents.fake import Call, FakeAgent, Script
from story_maker.observability.null import NullObservability
from story_maker.pipeline.acceptance import chapter_hash
from story_maker.store import models
from story_maker.store.brief_canon import (
    BriefRecipient,
    ConfirmedBrief,
    create_generation_candidate,
)
from story_maker.store.models import AuditLog, Brief, Chapter, Novel, User
from story_maker.store.session import unit_of_work
from story_maker.store.versions import publish

NOW = dt.datetime(2026, 9, 24, 12, 0)


@dataclasses.dataclass(frozen=True)
class MaskedNovel:
    novel_id: int
    version_id: int
    recipient_name: str
    birth_date: str
    recipient_character_id: int


def _build_masked_novel(
    session_factory: sessionmaker[Session],
    tmp_path: Path,
    *,
    owner_id: int,
    recipient_name: str,
    birth_date: dt.date,
) -> MaskedNovel:
    """Una novela publicada de una sola versión, con el destinatario en `Brief.content` (lo que
    lee `mask_for_novel`) y su nombre literal en cada capítulo (para comprobar la sustitución)."""
    with unit_of_work(session_factory) as uow:
        novel = Novel(user_id=owner_id, title=recipient_name, embedding_model="m1", created_at=NOW)
        uow.add(novel)
        uow.session.flush()
        uow.add(
            Brief(
                novel_id=novel.id,
                content={
                    "recipient": {"name": recipient_name, "birth_date": birth_date.isoformat()}
                },
                status="confirmed",
            )
        )
        novel_id = novel.id

    brief = ConfirmedBrief(
        recipient=BriefRecipient(recipient_name, 30, name_element_id=1, traits=()),
        close_ones=(),
    )
    with unit_of_work(session_factory) as uow:
        version_id = create_generation_candidate(uow, novel_id, brief, now=NOW).id

    with unit_of_work(session_factory) as uow:
        session = uow.session
        recipient = (
            session.query(models.Character)
            .filter_by(version_id=version_id, canonical_name=recipient_name)
            .one()
        )
        recipient_character_id = recipient.id
        for n in range(1, 3):
            title, text = f"Capítulo {n}", f"Capítulo {n} de {recipient_name}."
            uow.add(
                Chapter(
                    version_id=version_id,
                    number=n,
                    title=title,
                    text=text,
                    summary=f"Resumen {n}",
                    word_count=10,
                    content_hash=chapter_hash(title, text),
                )
            )

    pdf_path = tmp_path / f"{recipient_name}.pdf"
    pdf_path.write_bytes(f"%PDF-1.4 novela de {recipient_name}".encode())
    with unit_of_work(session_factory) as uow:
        publish(uow, version_id, pdf_path=str(pdf_path), now=NOW)

    return MaskedNovel(
        novel_id, version_id, recipient_name, birth_date.isoformat(), recipient_character_id
    )


@pytest.fixture
def owner(session_factory: sessionmaker[Session]) -> int:
    with unit_of_work(session_factory) as uow:
        user = User(email="mascara@example.com", password_hash="h", created_at=NOW)
        uow.add(user)
        uow.session.flush()
        return user.id


@pytest.fixture
def novel_one(session_factory: sessionmaker[Session], tmp_path: Path, owner: int) -> MaskedNovel:
    return _build_masked_novel(
        session_factory,
        tmp_path,
        owner_id=owner,
        recipient_name="Cayetana",
        birth_date=dt.date(2016, 4, 2),
    )


@pytest.fixture
def novel_two(session_factory: sessionmaker[Session], tmp_path: Path, owner: int) -> MaskedNovel:
    return _build_masked_novel(
        session_factory,
        tmp_path,
        owner_id=owner,
        recipient_name="Herminio",
        birth_date=dt.date(1988, 11, 20),
    )


def _captured(telemetry: NullObservability) -> str:
    """Todo lo que ha capturado el doble nulo, como un solo texto de búsqueda."""
    blob = []
    for trace in telemetry.traces.values():
        for span in trace.spans:
            blob.append(json.dumps(span.metadata, default=str, ensure_ascii=False))
    return "\n".join(blob)


async def test_traces_are_masked_and_never_carry_the_confirmation_code_or_the_pdf(
    client: TestClient,
    session_factory: sessionmaker[Session],
    owner: int,
    novel_one: MaskedNovel,
    novel_two: MaskedNovel,
    fake: FakeAgent,
    telemetry: NullObservability,
    mcp_session,
) -> None:
    headers = owner_headers(owner)

    async with mcp_session(headers) as mcp:
        await mcp.call_tool(
            "get_chapter", {"novel_id": novel_one.novel_id, "version": 1, "chapter": 1}
        )
        await mcp.call_tool("list_novels", {})

    fake.script(
        "planner",
        "change",
        Script(
            steps=(
                Call(
                    "propose_change",
                    {
                        "changes": [],
                        "new_fact": {
                            "subject_type": "character",
                            "subject_id": novel_one.recipient_character_id,
                            "attribute": "trait",
                            "value": "le gustan las estrellas",
                        },
                    },
                ),
            )
        ),
    )
    async with mcp_session(headers) as mcp:
        proposal = (
            await mcp.call_tool(
                "request_change",
                {
                    "novel_id": novel_one.novel_id,
                    "selection": {
                        "type": "fragment",
                        "version": 1,
                        "chapter": 1,
                        "quote": "Capítulo 1",
                    },
                    "request": "añade un rasgo",
                },
            )
        ).structured_content
    code = proposal["code"]

    async with mcp_session(headers) as mcp:
        await mcp.call_tool("confirm_change", {"request_id": proposal["id"], "code": code})

    async with mcp_session(headers) as mcp:
        download = await mcp.call_tool(
            "download_novel", {"novel_id": novel_one.novel_id, "version": 1}
        )
    (content,) = download.content
    pdf_bytes = base64.b64decode(content.resource.blob)

    captured = _captured(telemetry)
    for novel in (novel_one, novel_two):
        assert novel.recipient_name not in captured
        assert novel.birth_date not in captured
    assert code not in captured
    assert content.resource.blob not in captured

    with session_factory() as session:
        rows = session.query(AuditLog).filter(AuditLog.origin == "mcp_write").all()
    for row in rows:
        assert code not in json.dumps(row.detail, default=str)
        assert code not in (row.rule or "")

    download_span = next(
        span
        for trace in telemetry.traces.values()
        for span in trace.spans
        if span.name == "tool:download_novel"
    )
    assert download_span.metadata["output"] == {
        "version": 1,
        "content_type": "application/pdf",
        "size": len(pdf_bytes),
    }

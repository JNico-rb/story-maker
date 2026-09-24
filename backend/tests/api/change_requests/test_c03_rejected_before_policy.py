"""014-C03 — Lo que no admite una petición se rechaza antes de la policy: ni solicitud, ni sesión
de rol, ni decisión en el audit log, ni traza."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import FakeAgent
from story_maker.api.interview import MAX_MESSAGE_CHARS
from story_maker.observability.null import NullObservability
from story_maker.store import models
from story_maker.store.brief_canon import (
    BriefRecipient,
    ConfirmedBrief,
    create_generation_candidate,
)
from story_maker.store.session import unit_of_work

from .conftest import (
    NOW,
    F,
    fact_selection,
    fragment_selection,
    headers,
    propose,
    publish_copy,
    rename,
)


def _post(
    client: TestClient, novel_id: int, user_id: int, selection: dict[str, Any], request: str
) -> int:
    response = client.post(
        f"/api/novels/{novel_id}/change-requests",
        json={"selection": selection, "request": request},
        headers=headers(user_id),
    )
    return response.status_code


def _assert_nothing_left(
    session_factory: sessionmaker[Session], telemetry: NullObservability
) -> None:
    with session_factory() as session:
        assert session.query(models.ChangeRequest).count() == 0
        assert session.query(models.RoleSession).count() == 0
        assert session.query(models.AuditLog).count() == 0
    assert telemetry.traces == {}


def _novel_without_published_version(
    session_factory: sessionmaker[Session], user_id: int, *, with_candidate: bool
) -> int:
    with unit_of_work(session_factory) as uow:
        novel = models.Novel(user_id=user_id, title=None, embedding_model="M1", created_at=NOW)
        uow.add(novel)
        uow.session.flush()
        status = "confirmed" if with_candidate else "draft"
        uow.add(models.Brief(novel_id=novel.id, content={}, status=status))
        novel_id = novel.id
    if with_candidate:
        brief = ConfirmedBrief(recipient=BriefRecipient("Ada", 30, name_element_id=1, traits=()))
        with unit_of_work(session_factory) as uow:
            create_generation_candidate(uow, novel_id, brief, now=NOW)
    return novel_id


@pytest.mark.parametrize("with_candidate", [False, True], ids=["borrador", "generación a medias"])
def test_a_novel_without_published_version_answers_409(
    with_candidate: bool,
    client: TestClient,
    f: F,
    session_factory: sessionmaker[Session],
    telemetry: NullObservability,
) -> None:
    novel_id = _novel_without_published_version(
        session_factory, f.user_a, with_candidate=with_candidate
    )
    with session_factory() as session:
        before = session.query(models.AuditLog).count()

    status = _post(client, novel_id, f.user_a, fact_selection(f.toby_name_fact), "un cambio")

    assert status == 409
    with session_factory() as session:
        assert session.query(models.ChangeRequest).count() == 0
        assert session.query(models.AuditLog).count() == before
    assert telemetry.traces == {}


@pytest.mark.parametrize("kind", ["hecho", "fragmento"])
def test_a_selection_from_a_published_version_that_is_no_longer_current_answers_409(
    kind: str,
    client: TestClient,
    f: F,
    session_factory: sessionmaker[Session],
    telemetry: NullObservability,
) -> None:
    publish_copy(session_factory, f.v1_id)
    selection = fact_selection(f.toby_name_fact) if kind == "hecho" else fragment_selection(2)

    assert _post(client, f.novel_id, f.user_a, selection, "un cambio") == 409
    _assert_nothing_left(session_factory, telemetry)


def test_a_quote_that_is_not_literal_in_its_chapter_answers_422(
    client: TestClient, f: F, session_factory: sessionmaker[Session], telemetry: NullObservability
) -> None:
    selection = fragment_selection(3, "Toby ladra a su lado.")

    assert _post(client, f.novel_id, f.user_a, selection, "un cambio") == 422
    _assert_nothing_left(session_factory, telemetry)


def test_a_quote_with_other_spacing_is_still_literal(
    client: TestClient, f: F, fake: FakeAgent
) -> None:
    propose(fake, rename(f.toby_name_fact, "Nala"))
    selection = fragment_selection(2, "Ada   camina por\nla ciudad.")

    assert _post(client, f.novel_id, f.user_a, selection, "el perro se llama Nala") == 201


@pytest.mark.parametrize(
    "selection",
    [
        fragment_selection(0),
        fragment_selection(11),
        {"type": "fact", "fact_id": 999_999},
        {"type": "chapter", "chapter": 3},
        {"fact_id": 1},
    ],
    ids=["capítulo 0", "capítulo 11", "hecho inexistente", "ni fragmento ni hecho", "sin tipo"],
)
def test_a_selection_out_of_range_or_of_no_version_of_the_novel_answers_422(
    selection: dict[str, Any],
    client: TestClient,
    f: F,
    session_factory: sessionmaker[Session],
    telemetry: NullObservability,
) -> None:
    assert _post(client, f.novel_id, f.user_a, selection, "un cambio") == 422
    _assert_nothing_left(session_factory, telemetry)


def test_a_fact_of_another_novel_answers_422(
    client: TestClient, f: F, session_factory: sessionmaker[Session], telemetry: NullObservability
) -> None:
    other_novel = _novel_without_published_version(session_factory, f.user_a, with_candidate=True)
    with session_factory() as session:
        foreign = (
            session.query(models.Fact)
            .join(models.Version, models.Version.id == models.Fact.version_id)
            .filter(models.Version.novel_id == other_novel)
            .first()
        )
        assert foreign is not None
        foreign_id = foreign.id

    assert _post(client, f.novel_id, f.user_a, fact_selection(foreign_id), "un cambio") == 422
    _assert_nothing_left(session_factory, telemetry)


@pytest.mark.parametrize(
    "request_text", ["", "   ", "x" * (MAX_MESSAGE_CHARS + 1)], ids=["vacía", "blanca", "larga"]
)
def test_an_empty_or_too_long_request_answers_422(
    request_text: str,
    client: TestClient,
    f: F,
    session_factory: sessionmaker[Session],
    telemetry: NullObservability,
) -> None:
    selection = fact_selection(f.toby_name_fact)

    assert _post(client, f.novel_id, f.user_a, selection, request_text) == 422
    _assert_nothing_left(session_factory, telemetry)


def test_a_request_of_exactly_the_boundary_length_passes(
    client: TestClient, f: F, fake: FakeAgent
) -> None:
    propose(fake, rename(f.toby_name_fact, "Nala"))
    request_text = "x" * MAX_MESSAGE_CHARS

    assert (
        _post(client, f.novel_id, f.user_a, fact_selection(f.toby_name_fact), request_text) == 201
    )


@pytest.mark.parametrize("whose", ["otro cliente", "inexistente"])
def test_a_novel_of_another_client_or_missing_answers_404(
    whose: str,
    client: TestClient,
    f: F,
    session_factory: sessionmaker[Session],
    telemetry: NullObservability,
) -> None:
    novel_id, user_id = (f.novel_id, f.user_b) if whose == "otro cliente" else (999_999, f.user_a)

    assert _post(client, novel_id, user_id, fact_selection(f.toby_name_fact), "un cambio") == 404
    _assert_nothing_left(session_factory, telemetry)

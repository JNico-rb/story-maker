"""`GET /api/novels/{id}/versions[/{v}][/pdf]` (013-C11 a 013-C15)."""

from __future__ import annotations

import datetime as dt
import hashlib
import itertools
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from tests.render.novela_fixture import Novela, build_novela

from story_maker.api.app import create_app
from story_maker.api.auth import create_access_token
from story_maker.store import models
from story_maker.store.brief_canon import (
    BriefRecipient,
    ConfirmedBrief,
    create_generation_candidate,
)
from story_maker.store.session import create_schema, make_engine, make_session_factory, unit_of_work
from story_maker.store.versions import publish

JWT_SECRET = "x" * 32
NOW = dt.datetime(2026, 9, 24, 11, 0)
_emails = itertools.count(1)


@pytest.fixture
def session_factory(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = make_engine(tmp_path / "story-maker.db")
    create_schema(engine)
    yield make_session_factory(engine)
    engine.dispose()


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> TestClient:
    return TestClient(create_app(session_factory=session_factory, jwt_secret=JWT_SECRET))


@pytest.fixture
def novela(session_factory: sessionmaker[Session]) -> Novela:
    return build_novela(session_factory)


def _headers(user_id: int) -> dict[str, str]:
    now = dt.datetime.now(dt.UTC)
    token = create_access_token(user_id, JWT_SECRET, 24, now)
    return {"Authorization": f"Bearer {token}"}


def _register_foreign_client(client: TestClient) -> dict[str, str]:
    body = {"email": "cliente-b@example.com", "password": "contraseña-1"}
    client.post("/api/auth/register", json=body)
    token = client.post("/api/auth/login", json=body).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# --- 013-C13: listado de versiones publicadas ---------------------------------------------------


def test_c13_lists_published_versions_ascending_without_candidates(
    client: TestClient, novela: Novela
) -> None:
    response = client.get(
        f"/api/novels/{novela.novel_id}/versions", headers=_headers(novela.owner_user_id)
    )

    assert response.status_code == 200, response.text
    body = response.json()
    numbers = [v["number"] for v in body["versions"]]
    assert numbers == [1, 2]
    by_number = {v["number"]: v for v in body["versions"]}
    assert by_number[1]["changed_chapters"] == []
    assert by_number[2]["changed_chapters"] == [3, 7]


# --- 013-C14: detalle de una versión publicada -----------------------------------------------


def test_c14_detail_of_a_published_version_matches_the_version_view(
    client: TestClient, novela: Novela
) -> None:
    response = client.get(
        f"/api/novels/{novela.novel_id}/versions/2", headers=_headers(novela.owner_user_id)
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["version"] == 2
    view = body["view"]
    assert view["changed_chapters"] == [3, 7]
    assert len(view["chapters"]) == 10
    assert any(c["number"] == 3 and "Nala" in c["text"] for c in view["chapters"])
    names = {e["name"] for e in view["ficha"]}
    assert "Nala" in names
    assert "Toby" not in names


# --- 013-C15: lo que no existe, lo ajeno y lo mal formado --------------------------------------


def test_c15_missing_foreign_and_malformed_requests(client: TestClient, novela: Novela) -> None:
    owner_headers = _headers(novela.owner_user_id)
    foreign_headers = _register_foreign_client(client)
    base = f"/api/novels/{novela.novel_id}/versions"

    not_a_number = client.get(f"{base}/3", headers=owner_headers)
    assert not_a_number.status_code == 404

    foreign_detail = client.get(f"{base}/1", headers=foreign_headers)
    missing_novel_detail = client.get("/api/novels/999999/versions/1", headers=foreign_headers)
    assert foreign_detail.status_code == 404
    assert foreign_detail.text == missing_novel_detail.text

    foreign_list = client.get(base, headers=foreign_headers)
    assert foreign_list.status_code == 404

    for malformed in ("0", "uno"):
        response = client.get(f"{base}/{malformed}", headers=owner_headers)
        assert response.status_code == 422, malformed

    # K es una candidata: nunca alcanza la ruta por número (009-I1), se trata como inexistente.
    unpublished_number = client.get(f"{base}/3", headers=owner_headers)
    assert unpublished_number.status_code == 404


# --- 013-C11, 013-C12: el PDF por versión ------------------------------------------------------
#
# El resguardo de versiones (`version_guard`, 009-I1) rechaza escribir en una ya publicada: el
# `pdf_path` se fija al publicar, no después. `_publish_minimal_version` monta lo mínimo que
# necesita esta spec (013 no depende de 010/011/012 para tener una versión publicada).


def _publish_minimal_version(
    session_factory: sessionmaker[Session], *, pdf_path: str
) -> tuple[int, int]:
    email = f"cliente-pdf-{next(_emails)}@example.com"
    with unit_of_work(session_factory) as uow:
        user = models.User(email=email, password_hash="h", created_at=NOW)
        uow.add(user)
        uow.session.flush()
        novel = models.Novel(user_id=user.id, title=None, embedding_model="m1", created_at=NOW)
        uow.add(novel)
        uow.session.flush()
        owner_id, novel_id = user.id, novel.id

    brief = ConfirmedBrief(recipient=BriefRecipient("Ada", 30, name_element_id=1, traits=()))
    with unit_of_work(session_factory) as uow:
        version_id = create_generation_candidate(uow, novel_id, brief, now=NOW).id

    with unit_of_work(session_factory) as uow:
        for n in range(1, 11):
            title, text = f"Capítulo {n}", f"Texto del capítulo {n}."
            content_hash = hashlib.sha256(f"{title}\n{text}".encode()).hexdigest()
            uow.add(
                models.Chapter(
                    version_id=version_id,
                    number=n,
                    title=title,
                    text=text,
                    summary=f"Resumen {n}",
                    word_count=1200,
                    content_hash=content_hash,
                )
            )

    with unit_of_work(session_factory) as uow:
        publish(uow, version_id, pdf_path=pdf_path, now=NOW)

    return novel_id, owner_id


def test_c11_the_pdf_is_saved_per_version_and_served_as_is(
    client: TestClient, session_factory: sessionmaker[Session], tmp_path: Path
) -> None:
    pdf_bytes = b"%PDF-1.4 contenido de prueba de la version 1"
    pdf_path = tmp_path / "v1.pdf"
    pdf_path.write_bytes(pdf_bytes)
    novel_id, owner_id = _publish_minimal_version(session_factory, pdf_path=str(pdf_path))

    response = client.get(f"/api/novels/{novel_id}/versions/1/pdf", headers=_headers(owner_id))

    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == pdf_bytes


def test_c12_without_a_saved_pdf_the_route_answers_404(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    novel_id, owner_id = _publish_minimal_version(session_factory, pdf_path="nunca-se-escribio.pdf")

    response = client.get(f"/api/novels/{novel_id}/versions/1/pdf", headers=_headers(owner_id))

    assert response.status_code == 404

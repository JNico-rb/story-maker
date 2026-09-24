"""Propiedad: lo ajeno responde como inexistente (002-C15 a 002-C21, I3).

Al cerrar la 002 todavía no hay rutas de recurso (spec, autorrevisión), así que estos casos se
ejercen con rutas de prueba, montadas solo aquí, una por tipo de identificador de §15.7 —
novela, ejecución, solicitud de cambio, entrada de nivel `user`, hecho extraído, entrada de nivel
`novel`, número de versión y de capítulo — usando el mismo mecanismo (`get_current_user_id`,
`owned_or_404`) que usará cada ruta real de las specs siguientes."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.api.app import create_app
from story_maker.api.dependencies import get_current_user_id
from story_maker.api.ownership import NOT_FOUND_DETAIL, owned_or_404
from story_maker.store.models import (
    BannedTerm,
    ChangeRequest,
    Chapter,
    ExtractedFact,
    FreeText,
    Novel,
    Run,
    Version,
)
from story_maker.store.session import create_schema, make_engine, make_session_factory

JWT_SECRET = "x" * 32
NOW = dt.datetime(2026, 1, 1)


@contextmanager
def _session(request: Request) -> Iterator[Session]:
    """Sesión de lectura para las rutas de prueba; evita `Depends(get_session)` como valor por
    defecto anidado (falso positivo de ruff B008 en cierres)."""
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def _mount_novel_route(app: FastAPI) -> FastAPI:
    @app.get("/api/_test/novels/{novel_id}")
    def get_novel(
        novel_id: int, request: Request, user_id: int = Depends(get_current_user_id)
    ) -> dict[str, int]:
        with _session(request) as session:
            novel = owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
            return {"id": novel.id}

    return app


def _novel_owner(session: Session, novel_id: int) -> int | None:
    novel = session.get(Novel, novel_id)
    return novel.user_id if novel is not None else None


def _mount_run_route(app: FastAPI) -> FastAPI:
    @app.get("/api/_test/runs/{run_id}")
    def get_run(
        run_id: int, request: Request, user_id: int = Depends(get_current_user_id)
    ) -> dict[str, int]:
        with _session(request) as session:
            run = owned_or_404(
                session, Run, run_id, lambda r: _novel_owner(session, r.novel_id) == user_id
            )
            return {"id": run.id}

    return app


def _mount_change_request_route(app: FastAPI) -> FastAPI:
    @app.get("/api/_test/change-requests/{change_request_id}")
    def get_change_request(
        change_request_id: int, request: Request, user_id: int = Depends(get_current_user_id)
    ) -> dict[str, int]:
        with _session(request) as session:
            change_request = owned_or_404(
                session,
                ChangeRequest,
                change_request_id,
                lambda c: _novel_owner(session, c.novel_id) == user_id,
            )
            return {"id": change_request.id}

    return app


def _mount_banned_term_route(app: FastAPI) -> FastAPI:
    @app.get("/api/_test/banned-terms/{term_id}")
    def get_banned_term(
        term_id: int, request: Request, user_id: int = Depends(get_current_user_id)
    ) -> dict[str, int]:
        with _session(request) as session:
            term = owned_or_404(
                session,
                BannedTerm,
                term_id,
                lambda t: t.level == "user" and t.user_id == user_id,
            )
            return {"id": term.id}

    return app


def _free_text_novel_id(session: Session, free_text_id: int) -> int | None:
    free_text = session.get(FreeText, free_text_id)
    return free_text.novel_id if free_text is not None else None


def _mount_nested_routes(app: FastAPI) -> FastAPI:
    @app.get("/api/_test/novels/{novel_id}/extracted-facts/{fact_id}")
    def get_extracted_fact(
        novel_id: int, fact_id: int, request: Request, user_id: int = Depends(get_current_user_id)
    ) -> dict[str, int]:
        with _session(request) as session:
            novel = owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
            fact = owned_or_404(
                session,
                ExtractedFact,
                fact_id,
                lambda f: _free_text_novel_id(session, f.free_text_id) == novel.id,
            )
            return {"id": fact.id}

    @app.get("/api/_test/novels/{novel_id}/banned-terms/{term_id}")
    def get_novel_banned_term(
        novel_id: int, term_id: int, request: Request, user_id: int = Depends(get_current_user_id)
    ) -> dict[str, int]:
        with _session(request) as session:
            novel = owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
            term = owned_or_404(
                session,
                BannedTerm,
                term_id,
                lambda t: t.level == "novel" and t.novel_id == novel.id,
            )
            return {"id": term.id}

    @app.get("/api/_test/novels/{novel_id}/versions/{number}")
    def get_version(
        novel_id: int, number: int, request: Request, user_id: int = Depends(get_current_user_id)
    ) -> dict[str, int]:
        with _session(request) as session:
            novel = owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
            version = (
                session.query(Version)
                .filter(Version.novel_id == novel.id, Version.number == number)
                .one_or_none()
            )
            if version is None:
                raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
            return {"id": version.id, "number": version.number}

    @app.get("/api/_test/novels/{novel_id}/versions/{number}/chapters/{chapter_number}")
    def get_chapter(
        novel_id: int,
        number: int,
        chapter_number: int,
        request: Request,
        user_id: int = Depends(get_current_user_id),
    ) -> dict[str, int]:
        with _session(request) as session:
            novel = owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
            version = (
                session.query(Version)
                .filter(Version.novel_id == novel.id, Version.number == number)
                .one_or_none()
            )
            if version is None:
                raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
            chapter = (
                session.query(Chapter)
                .filter(Chapter.version_id == version.id, Chapter.number == chapter_number)
                .one_or_none()
            )
            if chapter is None:
                raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
            return {"id": chapter.id, "number": chapter.number}

    return app


def _mount_all_test_routes(app: FastAPI) -> FastAPI:
    _mount_novel_route(app)
    _mount_run_route(app)
    _mount_change_request_route(app)
    _mount_banned_term_route(app)
    _mount_nested_routes(app)
    return app


@pytest.fixture
def session_factory(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = make_engine(tmp_path / "story-maker.db")
    create_schema(engine)
    yield make_session_factory(engine)
    engine.dispose()


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> TestClient:
    app = create_app(session_factory=session_factory, jwt_secret=JWT_SECRET)
    _mount_all_test_routes(app)
    return TestClient(app)


def _register_and_login(client: TestClient, email: str) -> tuple[int, str]:
    register = client.post("/api/auth/register", json={"email": email, "password": "contraseña-1"})
    login = client.post("/api/auth/login", json={"email": email, "password": "contraseña-1"})
    return register.json()["id"], login.json()["access_token"]


def _create_novel(session_factory: sessionmaker[Session], user_id: int) -> int:
    session = session_factory()
    try:
        novel = Novel(user_id=user_id, title=None, embedding_model="m", created_at=NOW)
        session.add(novel)
        session.commit()
        return novel.id
    finally:
        session.close()


def _seed_world(session_factory: sessionmaker[Session], user_id: int) -> dict[str, int]:
    """Novela con brief, ejecución, solicitud de cambio, hecho extraído, prohibida de nivel
    `novel`, prohibida de nivel `user`, versión publicada con un capítulo, de un cliente
    (§ Mundo de partida de 002-C16 a 002-C21)."""
    session = session_factory()
    try:
        novel = Novel(user_id=user_id, title=None, embedding_model="m", created_at=NOW)
        session.add(novel)
        session.flush()

        version = Version(
            novel_id=novel.id,
            status="published",
            number=1,
            changed_chapters=[],
            created_at=NOW,
            published_at=NOW,
        )
        session.add(version)
        session.flush()

        chapter = Chapter(
            version_id=version.id,
            number=1,
            title="Capítulo 1",
            text="Érase una vez.",
            summary="Un comienzo.",
            word_count=1000,
            content_hash=f"hash-{novel.id}",
        )
        session.add(chapter)

        run = Run(novel_id=novel.id, type="generation", status="queued", resumes=0, created_at=NOW)
        session.add(run)

        change_request = ChangeRequest(
            novel_id=novel.id,
            base_version_id=version.id,
            selection_type="fragment",
            selection={"chapter": 1},
            request="cambia esto",
            status="proposed",
            created_at=NOW,
        )
        session.add(change_request)

        free_text = FreeText(
            novel_id=novel.id, content="una carta", discarded_instructions=None, created_at=NOW
        )
        session.add(free_text)
        session.flush()

        extracted_fact = ExtractedFact(
            free_text_id=free_text.id,
            subject="destinatario",
            attribute="nombre",
            value="Ada",
            quote="se llama Ada",
            verified=True,
            accepted=None,
            mandatory=False,
        )
        session.add(extracted_fact)

        novel_term = BannedTerm(
            level="novel",
            user_id=None,
            novel_id=novel.id,
            term=f"prohibida-novela-{novel.id}",
            type="word",
            keywords=None,
            normalized=f"prohibida-novela-{novel.id}",
        )
        session.add(novel_term)

        user_term = BannedTerm(
            level="user",
            user_id=user_id,
            novel_id=None,
            term=f"prohibida-{user_id}",
            type="word",
            keywords=None,
            normalized=f"prohibida-{user_id}",
        )
        session.add(user_term)

        session.commit()
        return {
            "novel_id": novel.id,
            "version_id": version.id,
            "chapter_id": chapter.id,
            "run_id": run.id,
            "change_request_id": change_request.id,
            "extracted_fact_id": extracted_fact.id,
            "novel_term_id": novel_term.id,
            "user_term_id": user_term.id,
        }
    finally:
        session.close()


def _seed_global_banned_term(session_factory: sessionmaker[Session]) -> int:
    session = session_factory()
    try:
        term = BannedTerm(
            level="global",
            user_id=None,
            novel_id=None,
            term="prohibida-global",
            type="word",
            keywords=None,
            normalized="prohibida-global",
        )
        session.add(term)
        session.commit()
        return term.id
    finally:
        session.close()


class FakeClock:
    def __init__(self, now: dt.datetime) -> None:
        self._now = now

    def __call__(self) -> dt.datetime:
        return self._now

    def set(self, now: dt.datetime) -> None:
        self._now = now


def test_token_is_checked_before_ownership(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    a_id, _a_token = _register_and_login(client, "cliente-a@example.com")
    novel_id = _create_novel(session_factory, a_id)
    missing_id = novel_id + 999

    without_token_own_id = client.get(f"/api/_test/novels/{novel_id}")
    without_token_missing_id = client.get(f"/api/_test/novels/{missing_id}")

    assert without_token_own_id.status_code == 401
    assert without_token_missing_id.status_code == 401

    t0 = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.UTC)
    clock = FakeClock(t0)
    clocked_app = create_app(session_factory=session_factory, jwt_secret=JWT_SECRET, clock=clock)
    _mount_novel_route(clocked_app)
    clocked_client = TestClient(clocked_app)
    _, a_token = _register_and_login(clocked_client, "otro-a@example.com")
    clock.set(t0 + dt.timedelta(hours=25))  # tras access_token_hours (24h): caducado

    expired_own_id = clocked_client.get(
        f"/api/_test/novels/{novel_id}", headers={"Authorization": f"Bearer {a_token}"}
    )
    expired_missing_id = clocked_client.get(
        f"/api/_test/novels/{missing_id}", headers={"Authorization": f"Bearer {a_token}"}
    )

    assert expired_own_id.status_code == 401
    assert expired_missing_id.status_code == 401


def test_someone_elses_resource_answers_as_nonexistent(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    a_id, a_token = _register_and_login(client, "cliente-a@example.com")
    _b_id, b_token = _register_and_login(client, "cliente-b@example.com")
    world_a = _seed_world(session_factory, a_id)
    headers_a = {"Authorization": f"Bearer {a_token}"}
    headers_b = {"Authorization": f"Bearer {b_token}"}

    cases = [
        (f"/api/_test/novels/{world_a['novel_id']}", "/api/_test/novels/999999"),
        (f"/api/_test/runs/{world_a['run_id']}", "/api/_test/runs/999999"),
        (
            f"/api/_test/change-requests/{world_a['change_request_id']}",
            "/api/_test/change-requests/999999",
        ),
        (f"/api/_test/banned-terms/{world_a['user_term_id']}", "/api/_test/banned-terms/999999"),
    ]
    for a_url, missing_url in cases:
        with_a_id = client.get(a_url, headers=headers_b)
        with_missing_id = client.get(missing_url, headers=headers_b)
        as_owner = client.get(a_url, headers=headers_a)

        assert with_a_id.status_code == 404, a_url
        assert with_missing_id.status_code == 404, missing_url
        assert with_a_id.text == with_missing_id.text, a_url
        assert as_owner.status_code == 200, a_url


def test_a_nested_resource_only_exists_within_its_parent(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    a_id, _a_token = _register_and_login(client, "cliente-a@example.com")
    b_id, b_token = _register_and_login(client, "cliente-b@example.com")
    world_a = _seed_world(session_factory, a_id)
    world_b = _seed_world(session_factory, b_id)
    headers_b = {"Authorization": f"Bearer {b_token}"}
    b_novel = world_b["novel_id"]

    fact_with_a_id = client.get(
        f"/api/_test/novels/{b_novel}/extracted-facts/{world_a['extracted_fact_id']}",
        headers=headers_b,
    )
    term_with_a_id = client.get(
        f"/api/_test/novels/{b_novel}/banned-terms/{world_a['novel_term_id']}", headers=headers_b
    )
    assert fact_with_a_id.status_code == 404
    assert term_with_a_id.status_code == 404

    version_response = client.get(f"/api/_test/novels/{b_novel}/versions/1", headers=headers_b)
    chapter_response = client.get(
        f"/api/_test/novels/{b_novel}/versions/1/chapters/1", headers=headers_b
    )

    assert version_response.status_code == 200
    assert version_response.json()["id"] == world_b["version_id"]
    assert version_response.json()["id"] != world_a["version_id"]

    assert chapter_response.status_code == 200
    assert chapter_response.json()["id"] == world_b["chapter_id"]
    assert chapter_response.json()["id"] != world_a["chapter_id"]

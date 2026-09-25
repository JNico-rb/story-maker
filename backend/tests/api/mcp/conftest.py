"""Fixtures del servidor MCP (015): un cliente MCP por HTTP contra la aplicación en proceso, sin
red real (`httpx.ASGITransport`), con el ciclo de vida de la app conducido a mano, porque el
`TestClient` síncrono no expone la sesión ASGI que pide `fastmcp.Client` (spec 015)."""

from __future__ import annotations

import asyncio
import datetime as dt
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastmcp.client import Client
from fastmcp.client.transports import StreamableHttpTransport
from sqlalchemy.orm import Session, sessionmaker
from tests.render.novela_fixture import Novela

from story_maker.api.auth import create_access_token
from story_maker.store.models import Brief, Novel, User
from story_maker.store.session import unit_of_work

MCP_URL = "http://testserver/mcp"
JWT_SECRET = "x" * 32
NOW = dt.datetime(2026, 9, 24, 12, 0)


@pytest.fixture
def mcp_app(client: TestClient) -> FastAPI:
    """La misma app que sirve `/api`, tal como la monta `create_app` (015-C01: mismo proceso)."""
    app: FastAPI = client.app  # type: ignore[assignment]
    return app


@asynccontextmanager
async def run_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Conduce el protocolo ASGI `lifespan` a mano: `httpx.ASGITransport` no lo dispara solo, y el
    gestor de sesión del transporte MCP lo necesita arrancado antes de la primera petición."""
    to_app: asyncio.Queue[dict[str, str]] = asyncio.Queue()
    to_app.put_nowait({"type": "lifespan.startup"})
    started = asyncio.Event()
    stopped = asyncio.Event()

    async def receive() -> dict[str, str]:
        return await to_app.get()

    async def send(message: dict[str, str]) -> None:
        if message["type"] == "lifespan.startup.complete":
            started.set()
        if message["type"] == "lifespan.shutdown.complete":
            stopped.set()

    task = asyncio.create_task(app({"type": "lifespan"}, receive, send))
    await started.wait()
    try:
        yield
    finally:
        to_app.put_nowait({"type": "lifespan.shutdown"})
        await stopped.wait()
        await task


def _httpx_client_factory(app: FastAPI) -> Callable[..., httpx.AsyncClient]:
    def factory(
        headers: dict[str, str] | None = None,
        timeout: httpx.Timeout | None = None,
        auth: httpx.Auth | None = None,
        **_: object,
    ) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
            headers=headers,
            timeout=timeout or httpx.Timeout(30),
            auth=auth,
        )

    return factory


def _token(headers: dict[str, str] | None) -> str | None:
    if headers is None:
        return None
    return headers["Authorization"].removeprefix("Bearer ")


@pytest.fixture
def mcp_session(
    mcp_app: FastAPI,
) -> Callable[[dict[str, str] | None], AsyncIterator[Client]]:
    """`async with mcp_session(auth_headers) as client:` conecta un `fastmcp.Client` por HTTP,
    con el ciclo de vida de la app arrancado alrededor, y la cabecera `Authorization` de esa
    conexión (o ninguna) — 015-C02, 015-C03: identidad por conexión, nunca fija entre pruebas."""
    factory = _httpx_client_factory(mcp_app)

    @asynccontextmanager
    async def make(auth_headers: dict[str, str] | None) -> AsyncIterator[Client]:
        headers = {"Authorization": f"Bearer {_token(auth_headers)}"} if auth_headers else None
        transport = StreamableHttpTransport(
            url=MCP_URL, headers=headers, httpx_client_factory=factory
        )
        async with run_lifespan(mcp_app), Client(transport) as client:
            yield client

    return make


def owner_headers(user_id: int) -> dict[str, str]:
    token = create_access_token(user_id, JWT_SECRET, 24, NOW)
    return {"Authorization": f"Bearer {token}"}


def _build_novela_with_real_pdfs(session_factory: sessionmaker[Session], tmp_path: Path) -> Novela:
    """Igual que `build_novela`, pero con un PDF real por versión: el resguardo de versiones
    (`version_guard`, 009-I1) no deja tocar `pdf_path` después de publicar, así que el camino se
    rehace aquí con la ruta real ya puesta en el propio `publish(...)` (015-C08)."""
    import datetime as _dt

    from tests.render.novela_fixture import (
        NOW as FIXTURE_NOW,
    )
    from tests.render.novela_fixture import (
        TITLE,
        _add_chapters,
        _brief,
        _character,
        _name_fact,
        _rewrite_chapter,
    )

    from story_maker.store import models
    from story_maker.store.brief_canon import create_generation_candidate
    from story_maker.store.story_bible import change_fact_value
    from story_maker.store.version_copy import copy_version
    from story_maker.store.versions import publish

    owner_email = f"cliente-mcp-{next(_emails_mcp)}@example.com"
    with unit_of_work(session_factory) as uow:
        user = User(email=owner_email, password_hash="h", created_at=FIXTURE_NOW)
        uow.add(user)
        uow.session.flush()
        novel = Novel(user_id=user.id, title=TITLE, embedding_model="m1", created_at=FIXTURE_NOW)
        uow.add(novel)
        uow.session.flush()
        uow.add(Brief(novel_id=novel.id, content={"dedication": "Para Ada."}, status="confirmed"))
        owner_id, novel_id = user.id, novel.id

    with unit_of_work(session_factory) as uow:
        v1_id = create_generation_candidate(uow, novel_id, _brief(), now=FIXTURE_NOW).id

    with unit_of_work(session_factory) as uow:
        session: Session = uow.session
        ada = _character(session, v1_id, "Ada")
        toby = _character(session, v1_id, "Toby")
        forest = models.Place(
            version_id=v1_id, canonical_name="el bosque", description="un claro", origin="invented"
        )
        uow.add(forest)
        session.flush()
        event = models.Event(
            version_id=v1_id,
            statement="Ada y Toby juegan en el bosque",
            moment=_dt.datetime(2026, 5, 1, 10, 0),
            place_id=forest.id,
            type="ordinary",
            analepsis=False,
            origin="recorded",
            chapter=4,
            beat=1,
        )
        uow.add(event)
        session.flush()
        uow.add(models.EventCharacter(event_id=event.id, character_id=ada.id))
        uow.add(models.EventCharacter(event_id=event.id, character_id=toby.id))

        ada_name = _name_fact(session, v1_id, ada.id)
        toby_name = _name_fact(session, v1_id, toby.id)
        for n in range(1, 11):
            uow.add(models.FactUsage(fact_id=ada_name.id, chapter=n))
        for n in (1, 3):
            uow.add(models.FactUsage(fact_id=toby_name.id, chapter=n))

        _add_chapters(uow, v1_id)

    v1_pdf = tmp_path / "v1.pdf"
    v1_pdf.write_bytes(b"%PDF-1.4 contenido de v1")
    with unit_of_work(session_factory) as uow:
        publish(uow, v1_id, pdf_path=str(v1_pdf), now=FIXTURE_NOW)

    with unit_of_work(session_factory) as uow:
        v2_id = copy_version(uow, v1_id, now=FIXTURE_NOW).version.id
        toby_v2 = (
            uow.session.query(models.Fact)
            .filter_by(version_id=v2_id, attribute="name", value="Toby")
            .one()
        )
        change_fact_value(uow, toby_v2.id, "Nala")

    with unit_of_work(session_factory) as uow:
        new_text = "Texto nuevo del capítulo {n}, con Nala."
        _rewrite_chapter(uow.session, v2_id, 3, "Capítulo 3", new_text.format(n=3))
        _rewrite_chapter(uow.session, v2_id, 7, "Capítulo 7", new_text.format(n=7))

    v2_pdf = tmp_path / "v2.pdf"
    v2_pdf.write_bytes(b"%PDF-1.4 contenido de v2")
    with unit_of_work(session_factory) as uow:
        publish(uow, v2_id, pdf_path=str(v2_pdf), now=FIXTURE_NOW)

    with unit_of_work(session_factory) as uow:
        k_id = copy_version(uow, v2_id, now=FIXTURE_NOW).version.id

    return Novela(novel_id, owner_id, owner_email, v1_id, v2_id, k_id)


_emails_mcp = iter(range(1, 10_000))


@pytest.fixture
def novela_p(session_factory: sessionmaker[Session], tmp_path: Path) -> Novela:
    """P de A: v1 y v2 publicadas (capítulos 3 y 7 cambiados; Toby en v1, Nala en v2), con PDF
    real por versión — «mundo de partida» de 015-C04 a 015-C08."""
    return _build_novela_with_real_pdfs(session_factory, tmp_path)


@pytest.fixture
def novel_s(session_factory: sessionmaker[Session], novela_p: Novela) -> int:
    """S de A: sin ninguna versión publicada (015-C04, 015-C05)."""
    with unit_of_work(session_factory) as uow:
        novel = Novel(
            user_id=novela_p.owner_user_id, title=None, embedding_model="m1", created_at=NOW
        )
        uow.add(novel)
        uow.session.flush()
        uow.add(Brief(novel_id=novel.id, content={}, status="draft"))
        novel_id = novel.id
    return novel_id


@pytest.fixture
def novela_p_headers(novela_p: Novela) -> dict[str, str]:
    return owner_headers(novela_p.owner_user_id)


@pytest.fixture
def raw_mcp_request(mcp_app: FastAPI) -> Callable[[], httpx.AsyncClient]:
    """Cliente HTTP crudo contra `/mcp`, para las pruebas de transporte (401 con el mismo cuerpo
    que `/api`) que no llegan a completar el protocolo MCP."""

    def make() -> httpx.AsyncClient:
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=mcp_app), base_url="http://testserver"
        )

    return make

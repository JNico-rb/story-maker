"""FastAPI mínima: salud, autenticación, OpenAPI, errores JSON y la SPA en el origen
(001-C17, 001-C18, 002)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from importlib.metadata import version
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.port import AgentPort, PolicyEngine
from story_maker.api.auth import Clock, utc_now
from story_maker.api.auth import router as auth_router
from story_maker.api.errors import validation_exception_handler
from story_maker.api.mcp.server import build_mcp_route
from story_maker.api.runs import router as runs_router
from story_maker.api.story_bible import router as story_bible_router
from story_maker.api.versions import router as versions_router
from story_maker.api.view import router as view_router
from story_maker.config import Config
from story_maker.observability.port import ObservabilityPort

Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]

RESERVED_PREFIXES = ("api", "view", "mcp")


def create_app(
    frontend_dist: Path | None = None,
    *,
    session_factory: sessionmaker[Session] | None = None,
    jwt_secret: str | None = None,
    access_token_hours: int = 24,
    clock: Clock = utc_now,
    agent_port: AgentPort | None = None,
    telemetry: ObservabilityPort | None = None,
    config: Config | None = None,
    workspace: Path | None = None,
    policy: PolicyEngine | None = None,
    lifespan: Lifespan | None = None,
) -> FastAPI:
    """`frontend_dist` es el build de la SPA; si no existe, el servidor arranca sin servirla.

    `session_factory` y `jwt_secret` habilitan el registro y el acceso (002); sin ellos, el
    servidor arranca igual, sin esas rutas, igual que sin `frontend_dist`. Las rutas de 008
    (novelas, entrevista, textos libres, brief, listas de prohibidas y audit log) y el servidor
    MCP en `/mcp` se montan solo cuando además llegan `agent_port`, `telemetry`, `config` y
    `workspace` (015-C01). `lifespan` es lo que vive con el servidor: en `serve`, el worker
    (031-C02); el ciclo de vida del servidor MCP se compone con él, no lo sustituye."""
    mcp_route = None
    if (
        session_factory is not None
        and jwt_secret is not None
        and agent_port is not None
        and telemetry is not None
        and config is not None
        and workspace is not None
    ):
        mcp_route, mcp_lifespan = build_mcp_route(
            session_factory=session_factory,
            jwt_secret=jwt_secret,
            clock=clock,
            agent_port=agent_port,
            telemetry=telemetry,
            config=config,
            workspace=workspace,
        )
        lifespan = _combine_lifespans(lifespan, mcp_lifespan)

    app = FastAPI(title="story-maker", lifespan=lifespan)
    # `exception_handler`, no `add_exception_handler`: su decorador tipa con un TypeVar genérico,
    # así que acepta un manejador específico de `RequestValidationError` sin que mypy strict se
    # queje de la contravarianza de `Callable[[Request, Exception], ...]`.
    app.exception_handler(RequestValidationError)(validation_exception_handler)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": version("story-maker")}

    if session_factory is not None and jwt_secret is not None:
        app.state.session_factory = session_factory
        app.state.jwt_secret = jwt_secret
        app.state.access_token_hours = access_token_hours
        app.state.clock = clock
        app.include_router(auth_router)
        app.include_router(runs_router)
        app.include_router(story_bible_router)
        app.include_router(versions_router)
        app.include_router(view_router)

        if agent_port is not None and telemetry is not None and config is not None:
            app.state.agent_port = agent_port
            app.state.telemetry = telemetry
            app.state.config = config
            app.state.workspace = workspace
            app.state.policy = policy
            _include_interview_routers(app)
            if mcp_route is not None:
                app.router.routes.append(mcp_route)

    if frontend_dist is not None and frontend_dist.is_dir():
        dist_resolved = frontend_dist.resolve()
        assets_dir = frontend_dist / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

        @app.get("/")
        def spa_index() -> FileResponse:
            index = frontend_dist / "index.html"
            if not index.is_file():
                raise HTTPException(status_code=404, detail="Not Found")
            return FileResponse(index)

        @app.get("/{full_path:path}")
        def spa_fallback(full_path: str) -> FileResponse:
            if full_path.split("/", 1)[0] in RESERVED_PREFIXES:
                raise HTTPException(status_code=404, detail="Not Found")
            # `..`, codificada o no, nunca sale del compilado (001-bug-C18b, `architecture.md`
            # §15.7): resuelta la ruta, se sirve solo si queda dentro de `dist_resolved`.
            candidate = (frontend_dist / full_path).resolve()
            if not candidate.is_relative_to(dist_resolved):
                raise HTTPException(status_code=404, detail="Not Found")
            if candidate.is_file():
                return FileResponse(candidate)
            index = frontend_dist / "index.html"
            if index.is_file():
                return FileResponse(index)
            raise HTTPException(status_code=404, detail="Not Found")

    return app


def _combine_lifespans(existing: Lifespan | None, mcp_lifespan: Lifespan) -> Lifespan:
    """El servidor MCP arranca y se detiene con la app (§14.4); si ya hay otro `lifespan` (el
    worker, en `serve`), los dos conviven, sin que uno sustituya al otro."""
    if existing is None:
        return mcp_lifespan

    @asynccontextmanager
    async def combined(app: FastAPI) -> AsyncIterator[None]:
        async with existing(app), mcp_lifespan(app):
            yield

    return combined


def _include_interview_routers(app: FastAPI) -> None:
    """Las rutas de la spec 008 (novelas, entrevista, brief); cada paso añade las suyas."""
    from story_maker.api.audit_log import router as audit_log_router
    from story_maker.api.banned_terms import router as banned_terms_router
    from story_maker.api.brief import router as brief_router
    from story_maker.api.change_requests import router as change_requests_router
    from story_maker.api.free_texts import router as free_texts_router
    from story_maker.api.interview import router as interview_router
    from story_maker.api.manual_edit import router as manual_edit_router
    from story_maker.api.novels import router as novels_router

    app.include_router(novels_router)
    app.include_router(interview_router)
    app.include_router(banned_terms_router)
    app.include_router(brief_router)
    app.include_router(free_texts_router)
    app.include_router(audit_log_router)
    app.include_router(change_requests_router)
    app.include_router(manual_edit_router)

"""FastAPI mínima: salud, autenticación, OpenAPI, errores JSON y la SPA en el origen
(001-C17, 001-C18, 002)."""

from __future__ import annotations

from importlib.metadata import version
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, sessionmaker

from story_maker.api.auth import Clock, utc_now
from story_maker.api.auth import router as auth_router

RESERVED_PREFIXES = ("api", "view", "mcp")


def create_app(
    frontend_dist: Path | None = None,
    *,
    session_factory: sessionmaker[Session] | None = None,
    jwt_secret: str | None = None,
    access_token_hours: int = 24,
    clock: Clock = utc_now,
) -> FastAPI:
    """`frontend_dist` es el build de la SPA; si no existe, el servidor arranca sin servirla.

    `session_factory` y `jwt_secret` habilitan el registro y el acceso (002); sin ellos, el
    servidor arranca igual, sin esas rutas, igual que sin `frontend_dist`."""
    app = FastAPI(title="story-maker")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": version("story-maker")}

    if session_factory is not None and jwt_secret is not None:
        app.state.session_factory = session_factory
        app.state.jwt_secret = jwt_secret
        app.state.access_token_hours = access_token_hours
        app.state.clock = clock
        app.include_router(auth_router)

    if frontend_dist is not None and frontend_dist.is_dir():
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
            candidate = frontend_dist / full_path
            if candidate.is_file():
                return FileResponse(candidate)
            index = frontend_dist / "index.html"
            if index.is_file():
                return FileResponse(index)
            raise HTTPException(status_code=404, detail="Not Found")

    return app

"""FastAPI mínima: salud, OpenAPI, errores en JSON y la SPA en el origen (001-C17, 001-C18)."""

from __future__ import annotations

from importlib.metadata import version
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RESERVED_PREFIXES = ("api", "view", "mcp")


def create_app(frontend_dist: Path | None = None) -> FastAPI:
    """`frontend_dist` es el build de la SPA; si no existe, el servidor arranca sin servirla."""
    app = FastAPI(title="story-maker")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": version("story-maker")}

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

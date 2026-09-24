"""El montaje de `serve` (031-C01): la API completa sobre la base de los ajustes, con los dobles
del puerto de agente (003) y de observabilidad (001). Ninguna prueba llama a un modelo (031-I2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import story_maker.settings as settings_module
from story_maker.agents.fake import FakeAgent
from story_maker.cli import DB_FILENAME, _build_server
from story_maker.composition import Adapters
from story_maker.observability.null import NullObservability
from story_maker.settings import Settings, load_settings
from story_maker.store.session import create_schema, make_engine

JWT_SECRET = "s" * 32


def make_settings(data_dir: Path, frontend_dist: Path) -> Settings:
    return load_settings(
        env={
            "STORY_MAKER_DATA_DIR": str(data_dir),
            "STORY_MAKER_FRONTEND_DIST": str(frontend_dist),
            "STORY_MAKER_CONFIG": str(settings_module.ROOT / "config.json"),
            "JWT_SECRET": JWT_SECRET,
            "FORMAL_VERIFIER": "local",
            "STORY_MAKER_BASE_URL": "http://127.0.0.1:8765",
        },
        env_file=data_dir / "sin.env",
    )


def fake_adapters(fake: FakeAgent | None = None) -> Adapters:
    return Adapters(agent=fake or FakeAgent())


def init_database(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    engine = make_engine(data_dir / DB_FILENAME)
    create_schema(engine)
    engine.dispose()


def served_app(settings: Settings, adapters: Adapters) -> FastAPI:
    """La aplicación tal como la construye `serve`."""
    app = _build_server(settings, NullObservability(), adapters).config.app
    assert isinstance(app, FastAPI)
    return app


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    path = tmp_path / "data"
    init_database(path)
    return path


@pytest.fixture
def frontend_dist(tmp_path: Path) -> Path:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><title>story-maker</title>", encoding="utf-8")
    return dist


def _token(client: TestClient) -> str:
    credentials = {"email": "cliente@example.com", "password": "una-contrasena-larga"}
    assert client.post("/api/auth/register", json=credentials).status_code == 201
    response = client.post("/api/auth/login", json=credentials)
    assert response.status_code == 200
    return str(response.json()["access_token"])


def test_serve_mounts_every_api_route_over_the_configured_database(
    data_dir: Path, frontend_dist: Path
) -> None:
    app = served_app(make_settings(data_dir, frontend_dist), fake_adapters())
    client = TestClient(app)

    headers = {"Authorization": f"Bearer {_token(client)}"}
    created = client.post("/api/novels", headers=headers)
    assert created.status_code == 201
    novel_id = created.json()["id"]

    assert client.get(f"/api/novels/{novel_id}", headers=headers).status_code == 200
    assert client.get(f"/api/novels/{novel_id}/brief", headers=headers).status_code == 200
    messages = client.get(f"/api/novels/{novel_id}/interview/messages", headers=headers)
    assert messages.status_code == 200
    assert client.get(f"/api/novels/{novel_id}/versions", headers=headers).status_code == 200
    assert client.get("/api/banned-terms", headers=headers).status_code == 200
    paths = set(app.openapi()["paths"])
    assert {
        "/api/novels/{novel_id}/free-texts",
        "/api/novels/{novel_id}/brief/confirm",
        "/api/novels/{novel_id}/runs",
        "/api/runs/{run_id}",
        "/api/runs/{run_id}/resume",
        "/api/novels/{novel_id}/versions/{number}",
        "/api/novels/{novel_id}/versions/{number}/pdf",
        "/view/versions/{version_id}",
        "/api/novels/{novel_id}/story-bible",
        "/api/novels/{novel_id}/audit-log",
    } <= paths
    assert "story-maker" in client.get("/").text


def test_serve_starts_without_the_spa_when_the_frontend_is_not_built(
    data_dir: Path, tmp_path: Path
) -> None:
    app = served_app(make_settings(data_dir, tmp_path / "sin-dist"), fake_adapters())
    client = TestClient(app)

    assert client.get("/").status_code == 404
    assert client.post("/api/auth/register", json={}).status_code == 422

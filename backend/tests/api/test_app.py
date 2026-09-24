"""Salud, esquema OpenAPI, errores JSON y la SPA en el mismo origen (001-C17, 001-C18)."""

from __future__ import annotations

from importlib.metadata import version
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from story_maker.api.app import create_app


@pytest.fixture
def frontend_dist(tmp_path: Path) -> Path:
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>spa</html>", encoding="utf-8")
    (dist / "assets" / "app.js").write_text("console.log('x')", encoding="utf-8")
    return dist


def test_health_answers_ok_with_the_package_version() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": version("story-maker")}


def test_health_needs_no_token() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200


def test_openapi_json_describes_the_whole_app_including_health() -> None:
    client = TestClient(create_app())

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/health" in response.json()["paths"]


def test_an_unknown_api_route_is_a_json_404_never_the_spa_index() -> None:
    client = TestClient(create_app())

    response = client.get("/api/no-existe")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert "detail" in response.json()
    assert response.text != "<html>spa</html>"


def test_the_spa_index_is_served_at_the_root(frontend_dist: Path) -> None:
    client = TestClient(create_app(frontend_dist))

    response = client.get("/")

    assert response.status_code == 200
    assert response.text == "<html>spa</html>"


def test_a_static_asset_is_served(frontend_dist: Path) -> None:
    client = TestClient(create_app(frontend_dist))

    response = client.get("/assets/app.js")

    assert response.status_code == 200
    assert response.text == "console.log('x')"


def test_a_client_route_that_is_not_a_file_falls_back_to_the_spa_index(
    frontend_dist: Path,
) -> None:
    client = TestClient(create_app(frontend_dist))

    response = client.get("/novelas/3")

    assert response.status_code == 200
    assert response.text == "<html>spa</html>"


@pytest.mark.parametrize("path", ["/api/x", "/view/x", "/mcp/x"])
def test_reserved_prefixes_without_anything_mounted_are_404(frontend_dist: Path, path: str) -> None:
    client = TestClient(create_app(frontend_dist))

    response = client.get(path)

    assert response.status_code == 404
    assert response.text != "<html>spa</html>"


def test_with_a_frontend_dist_that_does_not_exist_the_server_still_starts(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "no-existe"))

    health = client.get("/health")
    root = client.get("/")

    assert health.status_code == 200
    assert root.status_code == 404

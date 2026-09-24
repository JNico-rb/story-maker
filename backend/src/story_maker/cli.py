"""CLI `story-maker`; cada spec añade sus comandos."""

from __future__ import annotations

import asyncio
from importlib.metadata import version
from pathlib import Path
from typing import Annotated, cast
from urllib.parse import urlparse

import typer
import uvicorn

from story_maker.api.app import create_app
from story_maker.config import ConfigError, load_config
from story_maker.observability.null import NullObservability
from story_maker.settings import Settings, SettingsError, load_settings, resolve_paths
from story_maker.store.session import (
    create_schema,
    dense_channel_ok,
    make_engine,
    schema_diff,
)

app = typer.Typer(no_args_is_help=True, add_completion=False)

DB_FILENAME = "story-maker.db"


def _print_version(value: bool) -> None:
    if value:
        typer.echo(version("story-maker"))
        raise typer.Exit


@app.callback()
def main(
    _version: Annotated[
        bool,
        typer.Option(
            "--version", callback=_print_version, is_eager=True, help="Muestra la versión."
        ),
    ] = False,
) -> None:
    """Novelas personalizadas de regalo."""


def _db_path(data_dir: Path) -> Path:
    return data_dir / DB_FILENAME


@app.command(name="init-db")
def init_db_command(
    reset: Annotated[bool, typer.Option("--reset", help="Recrea la base si ya existe.")] = False,
) -> None:
    """Crea la base con el esquema completo; sin `--reset` no toca una base existente (C6, C7)."""
    try:
        settings = load_settings()
    except SettingsError as exc:
        for error in exc.errors:
            typer.echo(error)
        raise typer.Exit(1) from None

    db_path = _db_path(settings.data_dir)
    if db_path.exists() and not reset:
        typer.echo(f"La base ya existe en {db_path}; usa --reset para recrearla.")
        raise typer.Exit(1)

    settings.data_dir.mkdir(parents=True, exist_ok=True)
    if reset:
        for sidecar in settings.data_dir.glob(f"{DB_FILENAME}*"):
            sidecar.unlink()

    engine = make_engine(db_path)
    create_schema(engine)
    engine.dispose()
    typer.echo(str(db_path))


def _check_settings() -> tuple[Settings | None, str]:
    try:
        return load_settings(), "ajustes: ok"
    except SettingsError as exc:
        return None, "ajustes: fallo: " + "; ".join(exc.errors)


def _check_config(config_path: Path) -> str:
    try:
        load_config(config_path)
        return "config: ok"
    except ConfigError as exc:
        return "config: fallo: " + "; ".join(exc.errors)


def _check_database(data_dir: Path) -> str:
    db_path = _db_path(data_dir)
    if not db_path.is_file():
        return f"base de datos: fallo: no existe en {db_path}; ejecuta init-db"
    engine = make_engine(db_path)
    try:
        problems = schema_diff(engine)
        if problems:
            return "base de datos: fallo: " + "; ".join(problems) + "; ejecuta init-db --reset"
        if not dense_channel_ok(engine):
            return "base de datos: fallo: el canal denso no carga"
        return "base de datos: ok"
    finally:
        engine.dispose()


def _diagnostics() -> list[str]:
    """Una línea por comprobación; corre las que no dependen de una que ya ha fallado (C14)."""
    _, settings_line = _check_settings()
    data_dir, config_path = resolve_paths()
    return [
        settings_line,
        _check_config(config_path),
        _check_database(data_dir),
        "observabilidad: ok (doble nulo, sin Langfuse)",
    ]


def _has_failed(lines: list[str]) -> bool:
    return any(": fallo:" in line for line in lines)


@app.command(name="check-env")
def check_env_command() -> None:
    """Una línea por comprobación (ajustes, config, base y observabilidad); C14."""
    lines = _diagnostics()
    for line in lines:
        typer.echo(line)
    raise typer.Exit(1 if _has_failed(lines) else 0)


def _build_server(settings: Settings, observability: NullObservability) -> uvicorn.Server:
    parsed = urlparse(settings.base_url)
    # `settings.base_url` ya pasó la regex de C4 (http://host:puerto): los dos siempre están.
    host = cast(str, parsed.hostname)
    port = cast(int, parsed.port)
    fastapi_app = create_app(settings.frontend_dist)
    config = uvicorn.Config(fastapi_app, host=host, port=port, workers=1, log_level="warning")
    return uvicorn.Server(config)


async def _run_server(server: uvicorn.Server, observability: NullObservability) -> None:
    try:
        await server.serve()
    finally:
        observability.flush()


@app.command(name="serve")
def serve_command() -> None:
    """No arranca con config, ajustes o base inválidos (C15); un solo proceso, sin recarga (C16)."""
    lines = _diagnostics()
    for line in lines:
        typer.echo(line)
    if _has_failed(lines):
        raise typer.Exit(1)

    settings = load_settings()
    observability = NullObservability()
    server = _build_server(settings, observability)
    asyncio.run(_run_server(server, observability))

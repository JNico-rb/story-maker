"""CLI `story-maker`; cada spec añade sus comandos."""

from __future__ import annotations

import asyncio
from importlib.metadata import version
from pathlib import Path
from typing import Annotated, cast
from urllib.parse import urlparse

import typer
import uvicorn

from story_maker import settings as settings_module
from story_maker.api.app import create_app
from story_maker.config import ConfigError, load_config
from story_maker.observability.factory import build_langfuse_client, has_langfuse_vars
from story_maker.observability.langfuse_adapter import LangfuseObservability
from story_maker.observability.langfuse_adapter import auth_check as langfuse_auth_check
from story_maker.observability.null import NullObservability
from story_maker.observability.prompts import push_prompts
from story_maker.render.pdf import render_pdf
from story_maker.render.version_view import render_version_view
from story_maker.render.view_data import load_version_view_data
from story_maker.settings import Settings, SettingsError, load_settings, resolve_paths
from story_maker.store.models import Novel
from story_maker.store.session import (
    create_schema,
    dense_channel_ok,
    make_engine,
    make_session_factory,
    schema_diff,
)
from story_maker.store.versions import published_version

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


ObservabilityAdapter = NullObservability | LangfuseObservability


def _check_observability(settings: Settings | None) -> tuple[ObservabilityAdapter | None, str]:
    """Doble nulo salvo con las cuatro variables de Langfuse; si no, `auth_check` (004-C01..C06)."""
    if settings is None or not has_langfuse_vars(settings):
        return NullObservability(), "observabilidad: ok (doble nulo, sin Langfuse)"

    client = build_langfuse_client(settings)
    label = cast(str, settings.langfuse_prompt_label)
    problem = langfuse_auth_check(client, label)
    if problem is not None:
        return None, f"observabilidad: fallo: {problem}"
    return LangfuseObservability(client), "observabilidad: ok (Langfuse)"


def _diagnostics() -> tuple[list[str], ObservabilityAdapter | None]:
    """Una línea por comprobación; corre las que no dependen de una que ya ha fallado (C14)."""
    settings, settings_line = _check_settings()
    data_dir, config_path = resolve_paths()
    observability, observability_line = _check_observability(settings)
    lines = [
        settings_line,
        _check_config(config_path),
        _check_database(data_dir),
        observability_line,
    ]
    return lines, observability


def _has_failed(lines: list[str]) -> bool:
    return any(": fallo:" in line for line in lines)


@app.command(name="check-env")
def check_env_command() -> None:
    """Una línea por comprobación (ajustes, config, base y observabilidad); C14."""
    lines, _ = _diagnostics()
    for line in lines:
        typer.echo(line)
    raise typer.Exit(1 if _has_failed(lines) else 0)


def _build_server(settings: Settings, observability: ObservabilityAdapter) -> uvicorn.Server:
    parsed = urlparse(settings.base_url)
    # `settings.base_url` ya pasó la regex de C4 (http://host:puerto): los dos siempre están.
    host = cast(str, parsed.hostname)
    port = cast(int, parsed.port)
    fastapi_app = create_app(settings.frontend_dist)
    config = uvicorn.Config(fastapi_app, host=host, port=port, workers=1, log_level="warning")
    return uvicorn.Server(config)


async def _run_server(server: uvicorn.Server, observability: ObservabilityAdapter) -> None:
    try:
        await server.serve()
    finally:
        observability.flush()


@app.command(name="serve")
def serve_command() -> None:
    """No arranca con config, ajustes, base u observabilidad inválidos (C15); un proceso (C16)."""
    lines, observability = _diagnostics()
    for line in lines:
        typer.echo(line)
    if _has_failed(lines) or observability is None:
        raise typer.Exit(1)

    settings = load_settings()
    server = _build_server(settings, observability)
    asyncio.run(_run_server(server, observability))


prompts_app = typer.Typer(no_args_is_help=True, add_completion=False)
app.add_typer(prompts_app, name="prompts")


@prompts_app.command(name="push")
def prompts_push_command() -> None:
    """Sube el prompt de cada rol cuya huella cambió, con la etiqueta LANGFUSE_PROMPT_LABEL."""
    try:
        settings = load_settings()
    except SettingsError as exc:
        for error in exc.errors:
            typer.echo(error)
        raise typer.Exit(1) from None

    if not has_langfuse_vars(settings):
        typer.echo("prompts push: faltan las cuatro variables de Langfuse")
        raise typer.Exit(1)

    client = build_langfuse_client(settings)
    label = cast(str, settings.langfuse_prompt_label)
    prompts_dir = settings_module.ROOT / "backend" / "harness_workspace" / "prompts"
    pushed = push_prompts(prompts_dir, client, label)
    typer.echo("subidos: " + ", ".join(pushed) if pushed else "sin cambios")


@app.command(name="export-pdf")
def export_pdf_command(
    novel_id: Annotated[int, typer.Argument(help="Id de la novela.")],
    number: Annotated[int, typer.Argument(help="Número de la versión publicada.")],
) -> None:
    """Regenera desde su `VistaDeVersion` el PDF de una versión ya publicada y sustituye al
    guardado; no repite el gate ni cambia ningún dato de la versión (013-C17). Con una novela
    inexistente o una versión sin publicar, error con el motivo y ningún fichero se toca
    (013-C18). El backend solo escribe dentro de `STORY_MAKER_DATA_DIR` (013-I4)."""
    try:
        settings = load_settings()
    except SettingsError as exc:
        for error in exc.errors:
            typer.echo(error)
        raise typer.Exit(1) from None

    engine = make_engine(_db_path(settings.data_dir))
    try:
        session_factory = make_session_factory(engine)
        with session_factory() as session:
            if session.get(Novel, novel_id) is None:
                typer.echo(f"no existe la novela {novel_id}")
                raise typer.Exit(1)
            version = published_version(session, novel_id, number)
            if version is None:
                typer.echo(f"la novela {novel_id} no tiene publicada la versión {number}")
                raise typer.Exit(1)
            if version.pdf_path is None:
                typer.echo(f"la versión {number} de la novela {novel_id} no tiene PDF guardado")
                raise typer.Exit(1)

            path = Path(version.pdf_path).resolve()
            data_dir = settings.data_dir.resolve()
            if not path.is_relative_to(data_dir):
                typer.echo(f"{path} está fuera de STORY_MAKER_DATA_DIR ({data_dir}): no se escribe")
                raise typer.Exit(1)

            html = render_version_view(load_version_view_data(session, version))
            pdf_bytes = render_pdf(html)
            path.write_bytes(pdf_bytes)
        typer.echo(str(path))
    finally:
        engine.dispose()

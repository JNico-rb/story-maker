"""CLI `story-maker`; cada spec añade sus comandos."""

from __future__ import annotations

import asyncio
import subprocess
from importlib.metadata import version
from pathlib import Path
from typing import Annotated, cast
from urllib.parse import urlparse

import typer
import uvicorn
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from story_maker import settings as settings_module
from story_maker.api.app import create_app
from story_maker.config import ConfigError, load_config
from story_maker.observability.factory import build_langfuse_client, has_langfuse_vars
from story_maker.observability.langfuse_adapter import LangfuseObservability
from story_maker.observability.langfuse_adapter import auth_check as langfuse_auth_check
from story_maker.observability.null import NullObservability
from story_maker.observability.prompts import push_prompts
from story_maker.pipeline.runs import ResumeRejected, resume_run
from story_maker.render.pdf import render_pdf
from story_maker.render.version_view import render_version_view
from story_maker.render.view_data import load_version_view_data
from story_maker.settings import Settings, SettingsError, load_settings, resolve_paths
from story_maker.store.models import (
    Attempt,
    AuditLog,
    ExtractedFact,
    FreeText,
    Novel,
    RoleSession,
    Run,
    ValidatorResult,
)
from story_maker.store.session import (
    create_schema,
    dense_channel_ok,
    make_engine,
    make_session_factory,
    schema_diff,
    unit_of_work,
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


@app.command(name="resume")
def resume_command(
    run_id: Annotated[int, typer.Argument(help="Id de la ejecución interrumpida.")],
) -> None:
    """Vuelve a encolar una ejecución `interrupted` en su puesto; la ejecuta el worker del servidor
    en marcha cuando queda libre, sin reiniciarlo (011-C26). Otra cosa: código 1 y nada cambia."""
    try:
        settings = load_settings()
    except SettingsError as exc:
        for error in exc.errors:
            typer.echo(error)
        raise typer.Exit(1) from None

    engine = make_engine(_db_path(settings.data_dir))
    try:
        with unit_of_work(make_session_factory(engine)) as uow:
            position = resume_run(uow, run_id)
    except (LookupError, ResumeRejected) as exc:
        typer.echo(str(exc))
        raise typer.Exit(1) from None
    finally:
        engine.dispose()
    typer.echo(f"ejecución {run_id} en cola, posición {position}")


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


# --- `evals table` (020-C06..C09, 020-I2) -------------------------------------------------------
#
# Cada brief de eval es una `Novel` cuyo `title` es su slug (`ejemplo`, `infantil`, `boda`,
# `adversarial`, `temporal`), tal y como los crea `evals run` (020-C02..C05, fuera de este paso);
# `evals table` no depende de esa orden, solo de lo que ya haya en SQLite.

evals_app = typer.Typer(no_args_is_help=True, add_completion=False)
app.add_typer(evals_app, name="evals")

EVAL_BRIEF_SLUGS: tuple[str, ...] = ("ejemplo", "infantil", "boda", "adversarial", "temporal")

_BLOCKING = "blocking"
_SEMANTIC = "semantic"
_LINTER = "linter"
_FACTS_DISCARDED = "facts_discarded"
_AUDIT_FLAG = "audit_flag"
_AUDIT_DENY = "audit_deny"

# Orden y leyenda: `verification.md` §4.2 (a).
_VALIDATOR_ROWS: tuple[tuple[str, str], ...] = (
    ("`schema-brief`", _BLOCKING),
    ("`citas-verificadas` (hechos descartados)", _FACTS_DISCARDED),
    ("`schema-salida`", _BLOCKING),
    ("`outline`", _BLOCKING),
    ("`longitud-capitulo`", _BLOCKING),
    ("`nombres-exactos`", _BLOCKING),
    ("`palabras-prohibidas`", _BLOCKING),
    ("`elementos-obligatorios`", _BLOCKING),
    ("`rubrica-capitulo`", _SEMANTIC),
    ("`juez-novela`", _SEMANTIC),
    ("`cronologia-lean`", _BLOCKING),
    ("`revision-visual`", _BLOCKING),
    ("`pdf-enlaces`", _BLOCKING),
    ("`linter-repeticion`", _LINTER),
    ("`linter-legibilidad`", _LINTER),
    ("`linter-estilo-ia`", _LINTER),
    ("`linter-consistencia`", _LINTER),
    ("Detector de inyección (flags en `audit_log`)", _AUDIT_FLAG),
    ("Hook de policy (denegaciones en `audit_log`)", _AUDIT_DENY),
)


def _eval_novel(session: Session, slug: str) -> Novel | None:
    return session.scalar(select(Novel).where(Novel.title == slug))


def _eval_run(session: Session, novel_id: int) -> Run | None:
    return session.scalar(
        select(Run).where(Run.novel_id == novel_id, Run.type == "generation").order_by(Run.id)
    )


def _validator_results(session: Session, run_id: int, validator: str) -> list[ValidatorResult]:
    return list(
        session.scalars(
            select(ValidatorResult)
            .where(ValidatorResult.run_id == run_id, ValidatorResult.validator == validator)
            .order_by(ValidatorResult.id)
        )
    )


def _cell_blocking(results: list[ValidatorResult]) -> str:
    if not results:
        return "n/a"
    rejected = sum(1 for r in results if not r.passed)
    final = "pasa" if results[-1].passed else "falla"
    return f"{final} · {rejected}"


def _cell_semantic(results: list[ValidatorResult]) -> str:
    if not results:
        return "n/a"
    criteria = cast(list[float], results[-1].detail)
    average = sum(criteria) / len(criteria)
    minimum = min(criteria)
    minimum_text = str(int(minimum)) if float(minimum).is_integer() else str(minimum)
    return f"{average:.1f} ({minimum_text})"


def _cell_linter(results: list[ValidatorResult]) -> str:
    if not results:
        return "n/a"
    score = results[-1].score
    return "n/a" if score is None else str(int(score))


def _cell_facts_discarded(session: Session, novel_id: int) -> str:
    count = session.scalar(
        select(func.count(ExtractedFact.id))
        .join(FreeText, ExtractedFact.free_text_id == FreeText.id)
        .where(FreeText.novel_id == novel_id, ExtractedFact.accepted.is_(False))
    )
    return str(count or 0)


def _cell_audit(session: Session, novel_id: int, origin: str, decision: str) -> str:
    count = session.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.novel_id == novel_id,
            AuditLog.origin == origin,
            AuditLog.decision == decision,
        )
    )
    return str(count or 0)


def _cell(session: Session, novel: Novel | None, run: Run | None, validator: str, kind: str) -> str:
    if novel is None:
        return "n/a"
    if kind == _FACTS_DISCARDED:
        return _cell_facts_discarded(session, novel.id)
    if kind == _AUDIT_FLAG:
        return _cell_audit(session, novel.id, "free_text", "flag")
    if kind == _AUDIT_DENY:
        return _cell_audit(session, novel.id, "policy_hook", "deny")
    if run is None:
        return "n/a"
    results = _validator_results(session, run.id, validator)
    if kind == _BLOCKING:
        return _cell_blocking(results)
    if kind == _SEMANTIC:
        return _cell_semantic(results)
    return _cell_linter(results)


EvalBrief = tuple[Novel | None, Run | None]


def _table_a(session: Session, briefs: dict[str, EvalBrief]) -> str:
    header = (
        "| Validador | "
        + " | ".join(f"{i + 1} {slug}" for i, slug in enumerate(EVAL_BRIEF_SLUGS))
        + " |"
    )
    separator = "|" + "---|" * (len(EVAL_BRIEF_SLUGS) + 1)
    lines = [header, separator]
    for validator, kind in _VALIDATOR_ROWS:
        cells = [_cell(session, *briefs[slug], validator, kind) for slug in EVAL_BRIEF_SLUGS]
        lines.append(f"| {validator} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _row_status(_session: Session, _novel: Novel | None, run: Run | None) -> str:
    if run is None:
        return "n/a"
    if run.status == "failed":
        return f"failed ({run.reason})"
    return run.status


def _row_first_try(session: Session, _novel: Novel | None, run: Run | None) -> str:
    if run is None:
        return "n/a"
    count = session.scalar(
        select(func.count(Attempt.id)).where(
            Attempt.run_id == run.id,
            Attempt.evaluable == "chapter",
            Attempt.number == 1,
            Attempt.outcome == "accept",
        )
    )
    return str(count or 0)


def _row_gate_cycles(session: Session, _novel: Novel | None, run: Run | None) -> str:
    if run is None:
        return "n/a"
    count = session.scalar(
        select(func.count(Attempt.id)).where(
            Attempt.run_id == run.id, Attempt.evaluable == "gate_cycle"
        )
    )
    return str(count or 0)


def _role_sessions(session: Session, run: Run) -> list[RoleSession]:
    return list(
        session.scalars(
            select(RoleSession).where(RoleSession.run_id == run.id).order_by(RoleSession.id)
        )
    )


def _row_tokens(session: Session, _novel: Novel | None, run: Run | None) -> str:
    if run is None:
        return "n/a"
    sessions = _role_sessions(session, run)
    input_tokens = sum(s.input_tokens or 0 for s in sessions)
    output_tokens = sum(s.output_tokens or 0 for s in sessions)
    return f"{input_tokens} / {output_tokens}"


def _row_cost(session: Session, _novel: Novel | None, run: Run | None) -> str:
    if run is None:
        return "n/a"
    cost = sum(s.cost_usd or 0.0 for s in _role_sessions(session, run))
    return f"{cost:.4f}"


def _row_latency(session: Session, _novel: Novel | None, run: Run | None) -> str:
    if run is None:
        return "n/a"
    total = sum(s.latency_ms for s in _role_sessions(session, run))
    return f"{total} ms"


def _row_peak_tokens(session: Session, _novel: Novel | None, run: Run | None) -> str:
    # `architecture.md` §6.5: dentro de una ejecución hay como mucho una sesión de rol activa a
    # la vez, así que las sesiones de una misma ejecución nunca se solapan; el máximo de la suma
    # de las solapadas es, por tanto, el máximo individual.
    if run is None:
        return "n/a"
    sessions = _role_sessions(session, run)
    if not sessions:
        return "n/a"
    return str(max(s.reserved_tokens for s in sessions))


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],  # noqa: S607 — comando fijo, sin shell
            cwd=settings_module.ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return result.stdout.strip() or "n/a"
    except (OSError, subprocess.SubprocessError):
        return "n/a"


def _row_prompt_commit(session: Session, _novel: Novel | None, run: Run | None) -> str:
    if run is None:
        return "n/a"
    label = next(
        (s.prompt_version for s in _role_sessions(session, run) if s.prompt_version), "n/a"
    )
    return f"{label} · {_git_commit()}"


def _row_trace_id(session: Session, _novel: Novel | None, run: Run | None) -> str:
    # Con varias sesiones de rol en la ejecución, se lista la de la primera (por orden de
    # creación); sin ninguna, «—» — nunca una cadena vacía ni un error.
    if run is None:
        return "n/a"
    for role_session in _role_sessions(session, run):
        if role_session.trace_id:
            return role_session.trace_id
    return "—"


def _table_b(session: Session, briefs: dict[str, EvalBrief]) -> str:
    rows = (
        ("Estado final (`published`/`failed` + motivo)", _row_status),
        ("Capítulos aceptados al primer intento", _row_first_try),
        ("Ciclos de gate", _row_gate_cycles),
        ("Tokens (entrada / salida)", _row_tokens),
        ("Coste USD (Langfuse)", _row_cost),
        ("Latencia total", _row_latency),
        ("Pico de tokens concurrentes reservados", _row_peak_tokens),
        ("Etiqueta de prompts y commit", _row_prompt_commit),
        ("Identificador de traza", _row_trace_id),
    )
    header = (
        "| Métrica | "
        + " | ".join(f"{i + 1} {slug}" for i, slug in enumerate(EVAL_BRIEF_SLUGS))
        + " |"
    )
    separator = "|" + "---|" * (len(EVAL_BRIEF_SLUGS) + 1)
    lines = [header, separator]
    for label, row_fn in rows:
        cells = [row_fn(session, *briefs[slug]) for slug in EVAL_BRIEF_SLUGS]
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


@evals_app.command(name="table")
def evals_table_command() -> None:
    """Tabla (a) brief x validador y resumen (b) de `verification.md` §4.2, en Markdown, solo
    desde SQLite (020-C06..C09). Sin ejecuciones de evals, pide correr `evals run` y no escribe
    nada (020-C09)."""
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
            briefs: dict[str, EvalBrief] = {}
            found = False
            for slug in EVAL_BRIEF_SLUGS:
                novel = _eval_novel(session, slug)
                if novel is None:
                    briefs[slug] = (None, None)
                    continue
                found = True
                briefs[slug] = (novel, _eval_run(session, novel.id))

            if not found:
                typer.echo("sin ejecuciones de evals: ejecuta `story-maker evals run`")
                raise typer.Exit(1)

            table_a = _table_a(session, briefs)
            table_b = _table_b(session, briefs)
        typer.echo(table_a)
        typer.echo("")
        typer.echo(table_b)
    finally:
        engine.dispose()

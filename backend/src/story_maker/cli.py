"""CLI `story-maker`; cada spec añade sus comandos."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import socket
import subprocess
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Annotated, Any, cast
from urllib.parse import urlparse

import typer
import uvicorn
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from story_maker import settings as settings_module
from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.port import Agent, AgentPort, PolicyEngine
from story_maker.agents.sdk import SdkAgent
from story_maker.api.auth import normalize_email, utc_now
from story_maker.api.brief import brief_problems, build_brief_out
from story_maker.api.novels import EXTRACTOR_PROMPT_FILE
from story_maker.composition import (
    DB_FILENAME,
    Adapters,
    Mount,
    build_app,
    build_mount,
    create_mounted_app,
    real_adapters,
    workspace,
)
from story_maker.config import Config, ConfigError, load_config
from story_maker.domain.brief import BannedEntry, BriefContent
from story_maker.formal.defects import VALIDATOR as LEAN
from story_maker.interview.brief import TurnFailure, confirm_brief_status, run_turn
from story_maker.interview.free_text import FreeTextFailure, run_free_text
from story_maker.interview.import_brief import ImportFailure, ImportRejected, import_brief
from story_maker.interview.novels import brief_of, create_interview_novel, load_verified_facts
from story_maker.observability.factory import build_langfuse_client, has_langfuse_vars
from story_maker.observability.langfuse_adapter import LangfuseObservability
from story_maker.observability.langfuse_adapter import auth_check as langfuse_auth_check
from story_maker.observability.null import NullObservability
from story_maker.observability.port import ObservabilityPort
from story_maker.observability.prompts import push_prompts
from story_maker.pipeline.changes.confirm import ConfirmFailure, confirm_change
from story_maker.pipeline.changes.request import ProposalOut, RequestFailure, request_change
from story_maker.pipeline.changes.selection import FactSelection, FragmentSelection, Selection
from story_maker.pipeline.gate.phase import PDF_LINKS
from story_maker.pipeline.planning.attempts import OUTLINE_VALIDATOR
from story_maker.pipeline.queue import enqueue_generation
from story_maker.pipeline.runs import ResumeRejected, resume_run
from story_maker.policy.real_engine import RealPolicyEngine
from story_maker.render.pdf import render_pdf
from story_maker.render.version_view import render_version_view
from story_maker.render.view_data import load_version_view_data
from story_maker.reporting.metrics import build_report
from story_maker.settings import Settings, SettingsError, load_settings, resolve_paths
from story_maker.store.models import (
    Attempt,
    AuditLog,
    ExtractedFact,
    FreeText,
    Interview,
    InterviewMessage,
    Novel,
    RoleSession,
    Run,
    User,
    ValidatorResult,
    Version,
)
from story_maker.store.session import (
    create_schema,
    dense_channel_ok,
    make_engine,
    make_session_factory,
    schema_diff,
    unit_of_work,
)
from story_maker.store.users import get_user_by_email
from story_maker.store.versions import current_version, published_version
from story_maker.validators.chapter_length import LENGTH
from story_maker.validators.chapter_rubric import RUBRIC
from story_maker.validators.exact_names import EXACT_NAMES
from story_maker.validators.judge import VALIDATOR as JUDGE
from story_maker.validators.novel import BANNED_TERMS_VALIDATOR, MANDATORY_ELEMENTS_VALIDATOR

app = typer.Typer(no_args_is_help=True, add_completion=False)


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
    prompts_dir = settings_module.ROOT / "backend" / "harness_workspace" / "prompts"
    problem = langfuse_auth_check(client, label, prompts_dir)
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


def _base_url_address(settings: Settings) -> tuple[str, int]:
    parsed = urlparse(settings.base_url)
    # `settings.base_url` ya pasó la regex de C4 (http://host:puerto): los dos siempre están.
    return cast(str, parsed.hostname), cast(int, parsed.port)


def _build_server(
    settings: Settings, observability: ObservabilityAdapter, adapters: Adapters | None = None
) -> uvicorn.Server:
    """El servidor con el montaje de 031; `adapters` solo lo pasan las pruebas, con sus dobles."""
    host, port = _base_url_address(settings)
    app_config = load_config(settings.config_path)
    fastapi_app = build_app(
        settings, app_config, observability, adapters or real_adapters(settings, app_config)
    )
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


# --- `interview` (029-C01, C05, C06, C07, C08) -----------------------------------------------
#
# La orden usa los servicios de la 008 y de la 011 en el mismo proceso: sin servidor, sin rutas
# HTTP. No tiene reglas propias; cada rama del bucle llama directamente a `interview/` (`run_turn`,
# `run_free_text`, `load_verified_facts`, `brief_of`, `confirm_brief_status`), a `api/brief.py`
# (`build_brief_out`, `brief_problems`, ya puras, sin `Request`) y a `pipeline/queue.py`
# (`enqueue_generation`).


@dataclass
class _InterviewServices:
    session_factory: sessionmaker[Session]
    agent_port: AgentPort
    telemetry: ObservabilityPort
    policy: PolicyEngine
    config: Config
    workspace: Path


def _build_agent(settings: Settings, workspace: Path) -> Agent:
    return SdkAgent(settings, workspace=workspace)


def _build_interview_services(
    settings: Settings,
    config: Config,
    session_factory: sessionmaker[Session],
    telemetry: ObservabilityPort,
) -> _InterviewServices:
    workspace = settings_module.ROOT / "backend" / "harness_workspace"
    policy = RealPolicyEngine(session_factory, base_url=settings.base_url)
    agent_port = AgentPort(
        agent=_build_agent(settings, workspace),
        config=config,
        ceiling=TokenCeiling(config.token_ceiling),
        policy=policy,
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace,
    )
    return _InterviewServices(
        session_factory=session_factory,
        agent_port=agent_port,
        telemetry=telemetry,
        policy=policy,
        config=config,
        workspace=workspace,
    )


def _read_line() -> str | None:
    """`None` en EOF; Click sustituye `sys.stdin` en las pruebas, así que se lee de ahí y no del
    `input()` nativo (distinto en Windows cuando la entrada no es un terminal real)."""
    line = sys.stdin.readline()
    return None if line == "" else line.rstrip("\n")


async def _handle_turn(
    services: _InterviewServices, novel_id: int, user_id: int, text: str
) -> None:
    prompt = (services.workspace / "prompts" / "interviewer.md").read_text(encoding="utf-8")
    outcome = await run_turn(
        agent_port=services.agent_port,
        telemetry=services.telemetry,
        session_factory=services.session_factory,
        prompt=prompt,
        novel_id=novel_id,
        user_id=user_id,
        text=text,
        now=utc_now().replace(tzinfo=None),
    )
    if isinstance(outcome, TurnFailure):
        typer.echo("el turno no se guardó; repítelo")
        return
    typer.echo(outcome.reply)


async def _handle_free_text(
    services: _InterviewServices, novel_id: int, user_id: int, file_path: str
) -> None:
    """`/texto <fichero>`: el contenido va al extractor, nunca al entrevistador ni a la salida
    (029-C05); solo se imprimen el id y la cita de cada hecho verificado, pendiente de aceptar."""
    try:
        content = Path(file_path).read_text(encoding="utf-8")
    except OSError:
        typer.echo(f"no existe el fichero {file_path}")
        return

    prompt = (services.workspace / "prompts" / "extractor.md").read_text(encoding="utf-8")
    outcome = await run_free_text(
        agent_port=services.agent_port,
        telemetry=services.telemetry,
        policy=services.policy,
        session_factory=services.session_factory,
        prompt=prompt,
        novel_id=novel_id,
        user_id=user_id,
        text=content,
        now=utc_now().replace(tzinfo=None),
    )
    if isinstance(outcome, FreeTextFailure):
        typer.echo(outcome.reason)
        return
    for fact in outcome.verified_facts:
        typer.echo(f"{fact.id}: {fact.quote}")


def _fact_status(fact: ExtractedFact) -> str:
    if fact.accepted is None:
        return "pendiente"
    return "aceptado" if fact.accepted else "rechazado"


def _handle_list_facts(services: _InterviewServices, novel_id: int) -> None:
    """`/hechos` (029-C06): cada hecho extraído verificado, con su estado."""
    with services.session_factory() as session:
        facts = load_verified_facts(session, novel_id)
    for fact in facts:
        mark = " obligatorio" if fact.mandatory else ""
        typer.echo(
            f"{fact.id}: {_fact_status(fact)}{mark} · {fact.subject} {fact.attribute}={fact.value}"
        )


def _handle_fact_decision(
    services: _InterviewServices,
    novel_id: int,
    fact_id_text: str,
    *,
    accepted: bool | None = None,
    mandatory: bool | None = None,
) -> None:
    """`/aceptar`, `/rechazar` y `/obligatorio` (029-C06), como decide `patch_extracted_fact` de
    la 008 (008-C24): un hecho ajeno o inexistente, o un id que no es un número, no se encuentra;
    marcar obligatorio uno sin aceptar no se aplica."""
    try:
        fact_id = int(fact_id_text)
    except ValueError:
        typer.echo("hecho no encontrado")
        return

    with services.session_factory() as session:
        fact = (
            session.query(ExtractedFact)
            .join(FreeText, ExtractedFact.free_text_id == FreeText.id)
            .filter(
                FreeText.novel_id == novel_id,
                ExtractedFact.id == fact_id,
                ExtractedFact.verified.is_(True),
            )
            .one_or_none()
        )
        if fact is None:
            typer.echo("hecho no encontrado")
            return
        new_accepted = accepted if accepted is not None else bool(fact.accepted)
        if mandatory is not None:
            new_mandatory = mandatory
        elif accepted is False:
            new_mandatory = False
        else:
            new_mandatory = fact.mandatory

    if new_mandatory and not new_accepted:
        typer.echo("un hecho sin aceptar no puede ser obligatorio")
        return

    with unit_of_work(services.session_factory) as uow:
        fresh = uow.session.get(ExtractedFact, fact_id)
        if fresh is not None:
            if accepted is not None:
                fresh.accepted = accepted
                if accepted is False:
                    fresh.mandatory = False
            if mandatory is not None:
                fresh.mandatory = mandatory


def _handle_confirm(services: _InterviewServices, novel_id: int) -> None:
    """`/confirmar` (029-C07): con algo bloqueante, lo lista y no confirma (008-C09..C13); si no,
    pregunta y solo `s` confirma (008-C15). Tras confirmar, pregunta si lanzar la generación
    (029-C08); solo `s` la encola (011-C01)."""
    with services.session_factory() as session:
        novel = session.get(Novel, novel_id)
        if novel is None:  # pragma: no cover - la creó este mismo comando (029-C01)
            raise LookupError(f"novela {novel_id} no encontrada")
        brief = brief_of(session, novel_id)
        brief_out = build_brief_out(session, brief, novel, services.config.max_mandatory_elements)

    problems = brief_problems(brief_out)
    if problems:
        for problem in problems:
            typer.echo(str(problem["msg"]))
        return

    typer.echo("¿Confirmar el brief? [s/N]")
    answer = _read_line()
    if answer is None or answer.strip() != "s":
        typer.echo("el brief no se ha confirmado")
        return

    confirm_brief_status(services.session_factory, novel_id)
    typer.echo(f"novela {novel_id}: lista")

    typer.echo("¿Lanzar la generación? [s/N]")
    launch_answer = _read_line()
    if launch_answer is None or launch_answer.strip() != "s":
        return

    with unit_of_work(services.session_factory) as uow:
        run_id, position = enqueue_generation(uow, novel_id, now=utc_now())
    typer.echo(f"ejecución {run_id} en cola, posición {position}; la toma `story-maker serve`")


async def _interview_loop(services: _InterviewServices, novel_id: int, user_id: int) -> None:
    while True:
        line = _read_line()
        if line is None:
            return
        line = line.strip()
        if line == "/salir":
            return
        if not line:
            continue
        if line.startswith("/texto "):
            await _handle_free_text(services, novel_id, user_id, line[len("/texto ") :].strip())
        elif line == "/hechos":
            _handle_list_facts(services, novel_id)
        elif line.startswith("/aceptar "):
            _handle_fact_decision(
                services, novel_id, line[len("/aceptar ") :].strip(), accepted=True
            )
        elif line.startswith("/rechazar "):
            _handle_fact_decision(
                services, novel_id, line[len("/rechazar ") :].strip(), accepted=False
            )
        elif line.startswith("/obligatorio "):
            _handle_fact_decision(
                services, novel_id, line[len("/obligatorio ") :].strip(), mandatory=True
            )
        elif line == "/confirmar":
            _handle_confirm(services, novel_id)
        else:
            await _handle_turn(services, novel_id, user_id, line)


def _owned_novel_or_none(session: Session, novel_id: int, user_id: int) -> Novel | None:
    novel = session.get(Novel, novel_id)
    return novel if novel is not None and novel.user_id == user_id else None


def _print_interview_history(session_factory: sessionmaker[Session], novel_id: int) -> None:
    """El historial guardado de la entrevista, antes de seguir con el siguiente turno
    (029-C02)."""
    with session_factory() as session:
        interview = session.query(Interview).filter(Interview.novel_id == novel_id).one()
        messages = (
            session.query(InterviewMessage)
            .filter(InterviewMessage.interview_id == interview.id)
            .order_by(InterviewMessage.id)
            .all()
        )
    for message in messages:
        typer.echo(f"{message.author}: {message.text}")


@app.command(name="interview")
def interview_command(
    email: Annotated[str, typer.Option("--email", help="Email del cliente registrado.")],
    novel: Annotated[
        int | None, typer.Option("--novel", help="Id de una entrevista guardada, propia.")
    ] = None,
) -> None:
    """Entrevista por terminal sobre los servicios de la 008: cada línea es un turno; `/texto
    <fichero>` manda una carta al extractor; `/hechos`, `/aceptar`, `/rechazar` y `/obligatorio`
    gobiernan los hechos extraídos; `/confirmar` cierra el brief con un `s` explícito y, tras
    confirmarlo, lanza la generación con otro `s` explícito; `/salir` o el fin de la entrada
    terminan con 0 (029-C01, C05, C06, C07, C08). Sin `--novel`, crea una entrevista nueva
    (029-C01); con ella, sigue una guardada del mismo cliente, con su historial (029-C02). Un
    cliente sin registrar o una novela ajena o inexistente salen con 1 y no crean nada (029-C03)."""
    try:
        settings = load_settings()
    except SettingsError as exc:
        for error in exc.errors:
            typer.echo(error)
        raise typer.Exit(1) from None

    try:
        config = load_config(settings.config_path)
    except ConfigError as exc:
        for error in exc.errors:
            typer.echo(error)
        raise typer.Exit(1) from None

    observability, observability_line = _check_observability(settings)
    if observability is None:
        typer.echo(observability_line)
        raise typer.Exit(1)

    engine = make_engine(_db_path(settings.data_dir))
    try:
        session_factory = make_session_factory(engine)
        with session_factory() as session:
            user = get_user_by_email(session, normalize_email(email))
        if user is None:
            typer.echo("cliente no registrado")
            raise typer.Exit(1)

        services = _build_interview_services(settings, config, session_factory, observability)
        if novel is None:
            novel_id = create_interview_novel(
                session_factory,
                user_id=user.id,
                embedding_model=config.embedding_model,
                created_at=utc_now().replace(tzinfo=None),
            )
            typer.echo(str(novel_id))
        else:
            with session_factory() as session:
                owned = _owned_novel_or_none(session, novel, user.id)
            if owned is None:
                typer.echo("novela no encontrada")
                raise typer.Exit(1)
            novel_id = owned.id
            typer.echo(str(novel_id))
            _print_interview_history(session_factory, novel_id)
        asyncio.run(_interview_loop(services, novel_id, user.id))
    finally:
        engine.dispose()


# --- `change` (029-C09 a C14) ------------------------------------------------------------------
#
# La orden usa los servicios de la 014 en el mismo proceso, sin reglas propias: `request_change`
# decide si la petición se admite, la deniega o la interpreta, y `confirm_change` encola la
# ejecución. La CLI solo arma la selección (029-I1) y nunca imprime el código de confirmación
# (029-I3): lo guarda en memoria entre la propuesta y la pregunta.

CHANGE_PLANNER_PROMPT_FILE = "prompts/planner-change.md"
_REPEAT_LATER = "repítelo más tarde"
_NO_ROOM_DETAILS = ("no_room_in_time", "never_fits")


def _change_failure_text(detail: Any) -> str:
    """El motivo de una `RequestFailure` de la 014, en una línea (029-C12, C14)."""
    if isinstance(detail, dict) and "defects" in detail:
        return "; ".join(str(d) for d in detail["defects"])
    if isinstance(detail, dict):
        return "; ".join(f"{k}={v}" for k, v in detail.items())
    return str(detail)


def _print_change_proposal(outcome: ProposalOut) -> None:
    changes = cast(list[dict[str, Any]], outcome.proposal["changes"])
    for change in changes:
        typer.echo(f"hecho {change['fact_id']}: {change['old_value']} → {change['new_value']}")
    new_fact = cast(dict[str, Any] | None, outcome.proposal["new_fact"])
    if new_fact is not None:
        typer.echo(
            f"hecho nuevo: {new_fact['subject_type']} {new_fact['subject_id']} "
            f"{new_fact['attribute']}={new_fact['value']}"
        )
    typer.echo("capítulos afectados: " + ", ".join(str(c) for c in outcome.affected_chapters))


async def _run_change(
    services: _InterviewServices,
    novel_id: int,
    user_id: int,
    selection: Selection,
    request_text: str,
    base_number: int,
) -> None:
    prompt = (services.workspace / CHANGE_PLANNER_PROMPT_FILE).read_text(encoding="utf-8")
    outcome = await request_change(
        agent_port=services.agent_port,
        telemetry=services.telemetry,
        session_factory=services.session_factory,
        config=services.config,
        prompt=prompt,
        novel_id=novel_id,
        user_id=user_id,
        selection=selection,
        request=request_text,
        now=utc_now(),
    )
    if isinstance(outcome, RequestFailure):
        if outcome.status == 503 or (outcome.status, outcome.detail) == (422, "never_fits"):
            typer.echo(_REPEAT_LATER)
            raise typer.Exit(2)
        typer.echo(_change_failure_text(outcome.detail))
        raise typer.Exit(1)

    _print_change_proposal(outcome)
    typer.echo("¿Confirmar el cambio? [s/N]")
    answer = _read_line()
    if answer is None or answer.strip() != "s":
        typer.echo("el cambio no se ha confirmado")
        return

    confirmed = confirm_change(
        services.session_factory, request_id=outcome.id, code=outcome.code, now=utc_now()
    )
    if isinstance(confirmed, ConfirmFailure):  # pragma: no cover - recién propuesta, sin caducar
        typer.echo(confirmed.detail)
        raise typer.Exit(1)
    typer.echo(f"ejecución {confirmed} en cola, versión base {base_number}")


@app.command(name="change")
def change_command(
    novel_id: Annotated[int, typer.Argument(help="Id de la novela.")],
    request_text: Annotated[str, typer.Argument(help="La petición del cliente.")],
    email: Annotated[str, typer.Option("--email", help="Email del cliente registrado.")],
    fact: Annotated[int | None, typer.Option("--fact", help="Id del hecho a cambiar.")] = None,
    chapter: Annotated[
        int | None, typer.Option("--chapter", help="Capítulo del fragmento.")
    ] = None,
    fragment: Annotated[
        str | None, typer.Option("--fragment", help="Cita literal del fragmento.")
    ] = None,
) -> None:
    """Pide un cambio sobre un hecho (`--fact`) o un fragmento (`--chapter` y `--fragment`) de la
    novela vigente, con los servicios de la 014; confirma solo con un `s` explícito a la pregunta
    (029-C09 a C14, I1-I3)."""
    if fact is None and (chapter is None or fragment is None):
        typer.echo("indica --fact, o --chapter y --fragment")
        raise typer.Exit(1)

    try:
        settings = load_settings()
    except SettingsError as exc:
        for error in exc.errors:
            typer.echo(error)
        raise typer.Exit(1) from None

    try:
        config = load_config(settings.config_path)
    except ConfigError as exc:
        for error in exc.errors:
            typer.echo(error)
        raise typer.Exit(1) from None

    observability, observability_line = _check_observability(settings)
    if observability is None:
        typer.echo(observability_line)
        raise typer.Exit(1)

    engine = make_engine(_db_path(settings.data_dir))
    try:
        session_factory = make_session_factory(engine)
        with session_factory() as session:
            user = get_user_by_email(session, normalize_email(email))
        if user is None:
            typer.echo("novela no encontrada")
            raise typer.Exit(1)

        with session_factory() as session:
            owned = _owned_novel_or_none(session, novel_id, user.id)
            if owned is None:
                typer.echo("novela no encontrada")
                raise typer.Exit(1)
            base = current_version(session, owned.id)
        base_number = base.number or 0 if base is not None else 0

        selection: Selection
        if fact is not None:
            selection = FactSelection(type="fact", fact_id=fact)
        else:
            # Validado al principio de la orden: sin `--fact`, llegan los dos juntos.
            selection = FragmentSelection(
                type="fragment",
                version=base_number,
                chapter=cast(int, chapter),
                quote=cast(str, fragment),
            )

        services = _build_interview_services(settings, config, session_factory, observability)
        asyncio.run(_run_change(services, novel_id, user.id, selection, request_text, base_number))
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

# --- `evals run` (020-C01..C05) -----------------------------------------------------------------
#
# Cada fichero de `ejemplos/briefs/` es un brief de evaluación: el B0 de `BriefContent` (008), más
# `purpose`/`expect` (documentales, no entran en el import) y una forma más legible que la interna
# (`relationship` en vez de `relation`, rasgos y deseos de trama como texto llano, y los presentes
# o el excluido de un recuerdo referidos por la `key` de un allegado en vez de por su nombre).
# `eval_brief_content` traduce esa forma a lo que `brief_problems` y `import_brief` (008) esperan.

EVAL_BRIEFS_DIR = settings_module.ROOT / "ejemplos" / "briefs"
EVAL_MAX_MANDATORY_ELEMENTS = 8


def _eval_close_one(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": raw["name"],
        "relation": raw["relationship"],
        "species": raw["species"],
        "age": raw["age"],
        "birth_date": raw["birth_date"],
        "mandatory": raw["mandatory"],
    }


def _eval_recollection(raw: dict[str, Any], names_by_key: dict[str, str]) -> dict[str, Any]:
    excludes = raw.get("excludes")
    return {
        "statement": raw["statement"],
        "age": raw["age"],
        "year": raw["year"],
        "place": raw["place"],
        "present": [names_by_key[key] for key in raw.get("close_ones", [])],
        "excluded": names_by_key[excludes] if excludes else None,
        "mandatory": raw["mandatory"],
    }


def eval_brief_content(data: dict[str, Any]) -> tuple[BriefContent, list[BannedEntry], list[str]]:
    """El `BriefContent` (B0), sus entradas prohibidas (novel + user) y sus textos libres, desde
    la forma de fichero de un brief de `ejemplos/briefs/` (020-C01)."""
    brief = data["brief"]
    close_ones = brief.get("close_ones", [])
    names_by_key = {c["key"]: c["name"] for c in close_ones}
    content = BriefContent.model_validate(
        {
            "recipient": {
                "name": brief["recipient"]["name"],
                "age": brief["recipient"]["age"],
                "birth_date": brief["recipient"]["birth_date"],
                "traits": [
                    {"statement": trait, "mandatory": False}
                    for trait in brief["recipient"]["traits"]
                ],
                "relation": brief["recipient"]["relationship"],
            },
            "close_ones": [_eval_close_one(c) for c in close_ones],
            "recollections": [
                _eval_recollection(r, names_by_key) for r in brief.get("recollections", [])
            ],
            "occasion": brief["occasion"],
            "genre": brief["genre"],
            "tone": brief["tone"],
            "length": brief["length"],
            "dedication": brief["dedication"],
            "banned_asked": brief["banned_asked"],
            "plot_wishes": [{"statement": wish} for wish in brief.get("plot_wishes", [])],
        }
    )
    banned_entries = [
        BannedEntry(term=e["term"], type=e["type"], level="novel", keywords=e.get("keywords", []))
        for e in brief.get("banned_terms", [])
    ] + [
        BannedEntry(term=e["term"], type=e["type"], level="user", keywords=e.get("keywords", []))
        for e in data.get("user_banned_terms", [])
    ]
    free_texts = list(data.get("free_texts", []))
    return content, banned_entries, free_texts


@evals_app.command(name="run")
def evals_run_command(
    email: Annotated[
        str | None, typer.Option("--email", help="Cliente propietario de las evals.")
    ] = None,
) -> None:
    """Importa los cinco briefs de `ejemplos/briefs/` a nombre de `--email` y lanza su ejecución
    de generación, y procesa la cola hasta vaciarla (020-C03). Un brief que no pasa no para a los
    demás, pero la orden termina con 1 (020-C04); uno que ya tiene novela del cliente no se repite
    (020-C17). Nunca corre en la CI (020-C05); sin un cliente ya registrado, no crea nada
    (020-C02)."""
    if os.environ.get("CI") is not None:
        typer.echo("evals run no corre en la CI (verification.md §4.2 método 2)")
        raise typer.Exit(1)

    try:
        settings = load_settings()
    except SettingsError as exc:
        for error in exc.errors:
            typer.echo(error)
        raise typer.Exit(1) from None

    if not email:
        typer.echo("evals run necesita --email de un cliente ya registrado")
        raise typer.Exit(1)

    config, observability, user_id = _brief_services(settings, email)
    listener = _bind_base_url(settings)
    mount = build_mount(settings, config, observability, real_adapters(settings, config))
    try:
        launches, defects = asyncio.run(
            _serving_view(
                settings,
                config,
                observability,
                mount,
                listener,
                lambda: _run_evals(mount, config, observability, user_id),
            )
        )
        with mount.session_factory() as session:
            for launch in launches:
                status = session.get_one(Run, launch.run_id).status
                typer.echo(
                    f"{launch.slug}: novela {launch.novel_id}, ejecución {launch.run_id} ({status})"
                )
    finally:
        listener.close()
        mount.engine.dispose()
        observability.flush()
    for slug, defect in defects.items():
        typer.echo(f"{slug}: {defect}")
    if defects:
        raise typer.Exit(1)


def _brief_services(settings: Settings, email: str) -> tuple[Config, ObservabilityAdapter, int]:
    """La config, la observabilidad y el cliente propietario de las órdenes que importan un brief
    (`evals run`, `example`); sin cualquiera de los tres, código 1 y nada se crea (020-C02)."""
    engine = make_engine(_db_path(settings.data_dir))
    try:
        with make_session_factory(engine)() as session:
            user = session.scalar(select(User).where(User.email == email))
    finally:
        engine.dispose()
    if user is None:
        typer.echo(f"{email} no es un cliente registrado")
        raise typer.Exit(1)

    try:
        config = load_config(settings.config_path)
    except ConfigError as exc:
        for error in exc.errors:
            typer.echo(error)
        raise typer.Exit(1) from None
    observability, observability_line = _check_observability(settings)
    if observability is None:
        typer.echo(observability_line)
        raise typer.Exit(1)
    return config, observability, user.id


def eval_slug(path: Path) -> str:
    """`01-ejemplo.json` → `ejemplo`: el brief de eval de la novela que sale del fichero."""
    return path.stem.split("-", 1)[-1]


@dataclass(frozen=True)
class _EvalLaunch:
    slug: str | None
    novel_id: int
    run_id: int


def _import_body(
    content: BriefContent, banned_entries: list[BannedEntry], free_texts: list[str]
) -> dict[str, Any]:
    """El cuerpo de la importación de la API (008-C28): el B0, sus textos libres y sus prohibidas.
    Las `user_banned_terms` del fichero de un brief de eval no son del cliente que corre las
    evals: quedan de nivel `novel`, atadas a la novela que nace de ese brief, igual que las de
    nivel `novel` del propio fichero (020-C18)."""
    return {
        **content.model_dump(mode="json"),
        "banned_entries": [
            {"term": e.term, "type": e.type, "keywords": e.keywords} for e in banned_entries
        ],
        "free_texts": free_texts,
    }


def _problems_text(problems: list[dict[str, Any]]) -> str:
    return "; ".join(
        ".".join(str(part) for part in problem["loc"]) + f": {problem['msg']}"
        for problem in problems
    )


async def _launch_brief(
    mount: Mount,
    config: Config,
    telemetry: ObservabilityPort,
    user_id: int,
    path: Path,
    slug: str | None,
) -> _EvalLaunch | str:
    """El brief del fichero, importado como en la API (008), marcado con su brief de eval `slug`
    y con su generación encolada (011); o su defecto, sin novela (020-C04)."""
    try:
        content, banned_entries, free_texts = eval_brief_content(
            json.loads(path.read_text(encoding="utf-8"))
        )
    except ValidationError as exc:
        problems = [{"loc": error["loc"], "msg": error["msg"]} for error in exc.errors()]
        return f"no pasa schema-brief: {_problems_text(problems)}"
    except (ValueError, KeyError, TypeError) as exc:
        return f"no pasa schema-brief: {exc!r}"
    now = utc_now()
    outcome = await import_brief(
        agent_port=mount.agent_port,
        telemetry=telemetry,
        policy=mount.policy,
        session_factory=mount.session_factory,
        prompt=(workspace() / EXTRACTOR_PROMPT_FILE).read_text(encoding="utf-8"),
        user_id=user_id,
        embedding_model=config.embedding_model,
        max_mandatory_elements=config.max_mandatory_elements,
        body=_import_body(content, banned_entries, free_texts),
        now=now,
    )
    if isinstance(outcome, ImportRejected):
        return f"no pasa schema-brief: {_problems_text(outcome.problems)}"
    if isinstance(outcome, ImportFailure):
        return f"la extracción de sus textos libres falló: {outcome.reason}"
    with unit_of_work(mount.session_factory) as uow:
        uow.session.get_one(Novel, outcome.novel_id).eval_brief = slug
        run_id, _position = enqueue_generation(uow, outcome.novel_id, now=now)
    return _EvalLaunch(slug, outcome.novel_id, run_id)


async def _run_evals(
    mount: Mount, config: Config, telemetry: ObservabilityPort, user_id: int
) -> tuple[list[_EvalLaunch], dict[str, str]]:
    """Lanza cada brief de `EVAL_BRIEFS_DIR` y procesa la cola con el worker del montaje, sin
    atajos (020-I3), hasta que no queda nada en cola."""
    launches: list[_EvalLaunch] = []
    defects: dict[str, str] = {}
    for path in sorted(EVAL_BRIEFS_DIR.glob("*.json")):
        existing = _existing_eval_launch(mount.session_factory, user_id, eval_slug(path))
        if existing is not None:
            launches.append(existing)
            continue
        outcome = await _launch_brief(mount, config, telemetry, user_id, path, eval_slug(path))
        if isinstance(outcome, str):
            defects[eval_slug(path)] = outcome
        else:
            launches.append(outcome)
    await _drain_queue(mount)
    return launches, defects


def _existing_eval_launch(
    session_factory: sessionmaker[Session], user_id: int, slug: str
) -> _EvalLaunch | None:
    """La novela del cliente con ese brief de eval (de `example` o de un `evals run` anterior) y
    su ejecución de generación, que no se relanza: si quedó interrumpida, vuelve a la cola en su
    puesto, como con `resume` (011-C26; 020-C17)."""
    with unit_of_work(session_factory) as uow:
        novel = uow.session.scalar(
            select(Novel)
            .where(Novel.user_id == user_id, Novel.eval_brief == slug)
            .order_by(Novel.id)
        )
        if novel is None:
            return None
        run = uow.session.scalars(
            select(Run)
            .where(Run.novel_id == novel.id, Run.type == "generation")
            .order_by(Run.id.desc())
            .limit(1)
        ).one()
        if run.status == "interrupted":
            resume_run(uow, run.id)
        return _EvalLaunch(slug, novel.id, run.id)


def _bind_base_url(settings: Settings) -> socket.socket:
    """El puerto de `STORY_MAKER_BASE_URL`, tomado antes de crear nada; si no se puede (p. ej. un
    `serve` en marcha), código 1 y un mensaje que lo nombra (031-C06). Sin `SO_REUSEADDR`, que
    en Windows dejaría compartir el puerto de otro servidor."""
    host, port = _base_url_address(settings)
    try:
        return socket.create_server((host, port))
    except OSError as exc:
        typer.echo(
            f"no se puede servir la vista en el puerto {port} de STORY_MAKER_BASE_URL "
            f"({settings.base_url}): {exc}; ¿hay un `serve` en marcha?"
        )
        raise typer.Exit(1) from None


async def _serving_view[T](
    settings: Settings,
    config: Config,
    telemetry: ObservabilityPort,
    mount: Mount,
    listener: socket.socket,
    work: Callable[[], Awaitable[T]],
) -> T:
    """`work` con la API del mismo montaje servida en `listener`, para que la etapa 3 del gate
    navegue la vista (017-C02). El servidor no trae worker: solo toma la cola el del montaje;
    al terminar, se para (031-C06)."""
    fastapi_app = create_mounted_app(settings, config, telemetry, mount)
    server = uvicorn.Server(
        uvicorn.Config(fastapi_app, workers=1, log_level="warning", lifespan="off")
    )
    serving = asyncio.create_task(server.serve(sockets=[listener]))
    try:
        while not server.started and not serving.done():
            await asyncio.sleep(0.01)
        if not server.started:
            raise RuntimeError("el servidor de la vista no arrancó")
        return await work()
    finally:
        server.should_exit = True
        await asyncio.gather(serving, return_exceptions=True)


async def _drain_queue(mount: Mount) -> None:
    """El worker del montaje toma la cola hasta vaciarla, sin atajos (020-I3)."""
    while await mount.worker.run_next() is not None:
        pass


# --- `example` (020-C15) ----------------------------------------------------------------------

EXAMPLE_PDF = Path("ejemplos") / "novela-ejemplo.pdf"


async def _example(
    mount: Mount, config: Config, telemetry: ObservabilityPort, user_id: int, brief: Path
) -> _EvalLaunch | str:
    in_evals = brief.resolve().parent == EVAL_BRIEFS_DIR.resolve()
    slug = eval_slug(brief) if in_evals else None
    launch = await _launch_brief(mount, config, telemetry, user_id, brief, slug)
    if isinstance(launch, _EvalLaunch):
        await _drain_queue(mount)
    return launch


@app.command(name="example")
def example_command(
    brief: Annotated[Path, typer.Argument(help="Brief en JSON, con la forma de ejemplos/briefs/.")],
    email: Annotated[str, typer.Option("--email", help="Cliente propietario de la novela.")],
    out: Annotated[
        Path | None,
        typer.Option("--out", help="Dónde dejar el PDF; por defecto, ejemplos/novela-ejemplo.pdf."),
    ] = None,
) -> None:
    """Brief → novela publicada de `--email` → su PDF en `--out` (020-C15, `architecture.md`
    §15.8): el PDF que el gate guardó y pasó `pdf-enlaces`. Es la única orden que escribe fuera
    de `STORY_MAKER_DATA_DIR` (013-I4)."""
    try:
        settings = load_settings()
    except SettingsError as exc:
        for error in exc.errors:
            typer.echo(error)
        raise typer.Exit(1) from None

    config, observability, user_id = _brief_services(settings, email)
    target = out or settings_module.ROOT / EXAMPLE_PDF
    listener = _bind_base_url(settings)
    mount = build_mount(settings, config, observability, real_adapters(settings, config))
    try:
        launch = asyncio.run(
            _serving_view(
                settings,
                config,
                observability,
                mount,
                listener,
                lambda: _example(mount, config, observability, user_id, brief),
            )
        )
        if isinstance(launch, str):
            typer.echo(f"{brief}: {launch}")
            raise typer.Exit(1)
        with mount.session_factory() as session:
            run = session.get_one(Run, launch.run_id)
            version = session.scalar(
                select(Version).where(
                    Version.novel_id == launch.novel_id, Version.status == "published"
                )
            )
        if version is None or version.pdf_path is None:
            typer.echo(
                f"novela {launch.novel_id}: la ejecución {run.id} terminó {run.status} "
                f"({run.reason}); no hay PDF"
            )
            raise typer.Exit(1)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(version.pdf_path, target)
    finally:
        listener.close()
        mount.engine.dispose()
        observability.flush()
    typer.echo(f"novela {launch.novel_id}, ejecución {launch.run_id}: {target}")


_BLOCKING = "blocking"
_SEMANTIC = "semantic"
_LINTER = "linter"
_FACTS_DISCARDED = "facts_discarded"
_AUDIT_FLAG = "audit_flag"
_AUDIT_DENY = "audit_deny"

# Orden y leyenda: `verification.md` §4.2 (a): etiqueta de la fila, nombre con el que el
# productor guarda el `ResultadoDeValidador` y tipo de celda.
_VALIDATOR_ROWS: tuple[tuple[str, str | None, str], ...] = (
    ("`schema-brief`", "schema-brief", _BLOCKING),
    ("`citas-verificadas` (hechos descartados)", None, _FACTS_DISCARDED),
    ("`schema-salida`", "schema-salida", _BLOCKING),
    ("`outline`", OUTLINE_VALIDATOR, _BLOCKING),
    ("`longitud-capitulo`", LENGTH, _BLOCKING),
    ("`nombres-exactos`", EXACT_NAMES, _BLOCKING),
    ("`palabras-prohibidas`", BANNED_TERMS_VALIDATOR, _BLOCKING),
    ("`elementos-obligatorios`", MANDATORY_ELEMENTS_VALIDATOR, _BLOCKING),
    ("`rubrica-capitulo`", RUBRIC, _SEMANTIC),
    ("`juez-novela`", JUDGE, _SEMANTIC),
    ("`cronologia-lean`", LEAN, _BLOCKING),
    ("`revision-visual`", "revision-visual", _BLOCKING),
    ("`pdf-enlaces`", PDF_LINKS, _BLOCKING),
    ("`linter-repeticion`", "linter-repeticion", _LINTER),
    ("`linter-legibilidad`", "linter-legibilidad", _LINTER),
    ("`linter-estilo-ia`", "linter-estilo-ia", _LINTER),
    ("`linter-consistencia`", "linter-consistencia", _LINTER),
    ("Detector de inyección (flags en `audit_log`)", None, _AUDIT_FLAG),
    ("Hook de policy (denegaciones en `audit_log`)", None, _AUDIT_DENY),
)


def _eval_novel(session: Session, slug: str) -> Novel | None:
    return session.scalar(select(Novel).where(Novel.eval_brief == slug).order_by(Novel.id))


def _eval_run(session: Session, novel_id: int) -> Run | None:
    """La última ejecución de generación: la tabla muestra el estado actual del brief."""
    return session.scalar(
        select(Run)
        .where(Run.novel_id == novel_id, Run.type == "generation")
        .order_by(Run.id.desc())
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


def _detail_list(result: ValidatorResult, key: str) -> list[dict[str, Any]]:
    detail = result.detail
    if not isinstance(detail, dict):
        return []
    return cast(list[dict[str, Any]], detail.get(key) or [])


def _criteria_scores(result: ValidatorResult) -> list[float]:
    """Las puntuaciones por criterio: `criteria` en la rúbrica de capítulo (011), `parts` en el
    juez de novela (012)."""
    entries = _detail_list(result, "criteria") or _detail_list(result, "parts")
    return [float(entry["score"]) for entry in entries]


def _cell_semantic(results: list[ValidatorResult]) -> str:
    if not results:
        return "n/a"
    criteria = _criteria_scores(results[-1])
    if not criteria:
        return "n/a"
    average = sum(criteria) / len(criteria)
    minimum = min(criteria)
    minimum_text = str(int(minimum)) if minimum.is_integer() else str(minimum)
    return f"{average:.1f} ({minimum_text})"


def _cell_linter(results: list[ValidatorResult]) -> str:
    if not results:
        return "n/a"
    warnings = [d for d in _detail_list(results[-1], "defects") if not d.get("blocking")]
    return str(len(warnings))


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


def _cell(
    session: Session, novel: Novel | None, run: Run | None, validator: str | None, kind: str
) -> str:
    if novel is None:
        return "n/a"
    if kind == _FACTS_DISCARDED:
        return _cell_facts_discarded(session, novel.id)
    if kind == _AUDIT_FLAG:
        return _cell_audit(session, novel.id, "free_text", "flag")
    if kind == _AUDIT_DENY:
        return _cell_audit(session, novel.id, "policy_hook", "deny")
    if run is None or validator is None:
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
    for label, validator, kind in _VALIDATOR_ROWS:
        cells = [_cell(session, *briefs[slug], validator, kind) for slug in EVAL_BRIEF_SLUGS]
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
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


report_app = typer.Typer(no_args_is_help=True, add_completion=False)
app.add_typer(report_app, name="report")


@report_app.command(name="metrics")
def report_metrics_command(
    out: Annotated[
        Path | None, typer.Option("--out", help="Ruta del Markdown; por defecto docs/metrics.md.")
    ] = None,
) -> None:
    """Agrega `role_sessions` y `validator_results` en un Markdown determinista, sin red (030)."""
    try:
        settings = load_settings()
    except SettingsError as exc:
        for error in exc.errors:
            typer.echo(error)
        raise typer.Exit(1) from None

    out_path = out if out is not None else settings_module.ROOT / "docs" / "metrics.md"

    engine = make_engine(_db_path(settings.data_dir))
    try:
        session_factory = make_session_factory(engine)
        with session_factory() as session:
            report = build_report(session)
    finally:
        engine.dispose()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    typer.echo(str(out_path))

"""El montaje único de la aplicación que comparten `serve`, `example` y `evals run`
(`architecture.md` §1.4: un proceso; spec 031).

Monta cada pieza de las specs con sus dependencias reales: la API entera y el worker del mismo
proceso, que arranca con el servidor, toma la cola y se apaga con él (§9.1). Lo que sale del
proceso (el agente, Lean, el render del PDF y el modelo de incrustación) llega en `Adapters`,
que las pruebas sustituyen por sus dobles."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from story_maker import settings as settings_module
from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.port import Agent, AgentPort
from story_maker.agents.sdk import SdkAgent
from story_maker.api.app import create_app
from story_maker.api.auth import Clock, utc_now
from story_maker.config import Config
from story_maker.formal.candidate import CandidateVerification, verify_candidate
from story_maker.formal.verifier import FormalVerifier, make_formal_verifier
from story_maker.observability.port import ObservabilityPort, Trace
from story_maker.observability.roles import ROLE_LABELS
from story_maker.pipeline.gate.phase import Gate, PdfOutcome, PdfStage, VisualReviewOutcome
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.planning_seam import PlanningSeam
from story_maker.pipeline.production import Production, Prompts
from story_maker.pipeline.runs import naive
from story_maker.pipeline.windows import CandidateWindows, Retriever
from story_maker.pipeline.worker import Worker
from story_maker.policy.real_engine import RealPolicyEngine
from story_maker.render.pdf import render_pdf
from story_maker.render.pdf_links import check_pdf_links
from story_maker.render.version_view import render_version_view
from story_maker.render.view_data import load_version_view_data
from story_maker.retrieval.cards import sync_canon_cards
from story_maker.retrieval.embedding import EmbeddingModel
from story_maker.retrieval.fastembed_model import FastEmbedModel
from story_maker.retrieval.retriever import retrieve
from story_maker.settings import Settings
from story_maker.store.models import Version
from story_maker.store.session import make_engine, make_session_factory

DB_FILENAME = "story-maker.db"


@dataclass(frozen=True)
class Adapters:
    """Lo que sale del proceso; las pruebas lo sustituyen por sus dobles."""

    agent: Agent
    formal_verifier: FormalVerifier
    render_pdf: Callable[[str], bytes]
    embedder: EmbeddingModel


def workspace() -> Path:
    return settings_module.ROOT / "backend" / "harness_workspace"


def real_adapters(settings: Settings, config: Config) -> Adapters:
    """El agente de `LLM_PROVIDER` (§15.2), el verificador de `FORMAL_VERIFIER` y el modelo de
    incrustación local (§6.3)."""
    return Adapters(
        agent=SdkAgent(settings, workspace=workspace()),
        formal_verifier=make_formal_verifier(settings, config.verifier_timeout_seconds),
        render_pdf=render_pdf,
        embedder=FastEmbedModel(),
    )


def role_prompt(
    role: str, telemetry: ObservabilityPort, label: str | None
) -> tuple[str, str | None]:
    """El prompt del fichero del workspace y su versión de Langfuse con `label`; sin etiqueta o
    con el doble nulo, sin versión (§13.4, §13.6)."""
    text = (workspace() / "prompts" / f"{role}.md").read_text(encoding="utf-8")
    version = telemetry.get_prompt(ROLE_LABELS[role], label) if label else None
    return text, version


def card_retriever(embedder: EmbeddingModel) -> Retriever:
    def texts(
        session: Session, version_id: int, chapter: int, fragments: Sequence[str], top_k: int
    ) -> list[str]:
        cards = retrieve(session, version_id, chapter, fragments, top_k, embedder)
        return [card.text for card in cards]

    return texts


def pdf_stage(
    session_factory: sessionmaker[Session], data_dir: Path, render: Callable[[str], bytes]
) -> PdfStage:
    """La etapa 4 del gate: el PDF de la candidata, guardado por versión en el directorio de
    datos (§14.2), y `pdf-enlaces` sobre él. El render es síncrono: corre en otro hilo."""

    async def stage(version_id: int) -> PdfOutcome:
        with session_factory() as session:
            version = session.get_one(Version, version_id)
            html = render_version_view(load_version_view_data(session, version))
        try:
            pdf = await asyncio.to_thread(render, html)
        except Exception as exc:
            return PdfOutcome(None, detail=f"el PDF no se generó: {exc}")
        path = data_dir / "pdfs" / f"{version_id}.pdf"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(pdf)
        links = check_pdf_links(pdf)
        if links.passed:
            return PdfOutcome(str(path), True)
        broken = ", ".join(link.target for link in links.broken_links)
        detail = f"capítulos sin ancla: {links.missing_chapters}; enlaces rotos: {broken}"
        return PdfOutcome(str(path), False, detail)

    return stage


async def no_visual_review(run_id: int, trace: Trace) -> VisualReviewOutcome:
    """La etapa 3 (017) está fuera de alcance: el montaje no la arranca."""
    del run_id, trace
    return VisualReviewOutcome()


def build_worker(
    settings: Settings,
    config: Config,
    telemetry: ObservabilityPort,
    adapters: Adapters,
    agent_port: AgentPort,
    session_factory: sessionmaker[Session],
    clock: Clock,
) -> Worker:
    """El orquestador con sus tres fases: planificación (010), capítulos (011) y gate (012)."""
    label = settings.langfuse_prompt_label
    writer, writer_version = role_prompt("writer", telemetry, label)
    editor, editor_version = role_prompt("editor", telemetry, label)
    production = Production(
        port=agent_port,
        session_factory=session_factory,
        telemetry=telemetry,
        config=config,
        windows=CandidateWindows(retriever=card_retriever(adapters.embedder), top_k=config.top_k),
        cards=functools.partial(sync_canon_cards, embedder=adapters.embedder),
        clock=clock,
        prompts=Prompts(writer, editor, writer_version, editor_version),
    )

    async def lean(run_id: int) -> CandidateVerification:
        return await verify_candidate(
            session_factory,
            adapters.formal_verifier,
            run_id=run_id,
            data_dir=settings.data_dir,
            now=naive(clock()),
        )

    planner, planner_version = role_prompt("planner", telemetry, label)
    judge, judge_version = role_prompt("judge", telemetry, label)
    gate = Gate(
        production=production,
        lean=lean,
        visual_review=no_visual_review,
        pdf=pdf_stage(session_factory, settings.data_dir, adapters.render_pdf),
        judge_prompt=judge,
        judge_prompt_version=judge_version,
    )
    orchestrator = Orchestrator(
        production=production,
        planning=PlanningSeam(production, planner, planner_version),
        gate=gate,
    )
    return Worker(
        session_factory, orchestrator.execute, max_resumes=config.max_resumes, clock=clock
    )


@dataclass(frozen=True)
class Mount:
    """Las piezas que comparten el servidor, `evals run` y `example` sobre la misma base."""

    engine: Engine
    session_factory: sessionmaker[Session]
    policy: RealPolicyEngine
    agent_port: AgentPort
    worker: Worker


def build_mount(
    settings: Settings,
    config: Config,
    telemetry: ObservabilityPort,
    adapters: Adapters,
    *,
    clock: Clock = utc_now,
) -> Mount:
    """La base de `STORY_MAKER_DATA_DIR`, el motor de políticas, el puerto de agente y el worker."""
    engine = make_engine(settings.data_dir / DB_FILENAME)
    session_factory = make_session_factory(engine)
    policy = RealPolicyEngine(session_factory, base_url=settings.base_url)
    agent_port = AgentPort(
        agent=adapters.agent,
        config=config,
        ceiling=TokenCeiling(config.token_ceiling),
        policy=policy,
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace(),
    )
    worker = build_worker(settings, config, telemetry, adapters, agent_port, session_factory, clock)
    return Mount(engine, session_factory, policy, agent_port, worker)


def build_app(
    settings: Settings,
    config: Config,
    telemetry: ObservabilityPort,
    adapters: Adapters,
    *,
    clock: Clock = utc_now,
) -> FastAPI:
    """La API entera sobre la base de `STORY_MAKER_DATA_DIR`, con la SPA si está compilada, y el
    worker, que vive lo que vive el servidor."""
    mount = build_mount(settings, config, telemetry, adapters, clock=clock)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        task = asyncio.create_task(mount.worker.run_forever())
        try:
            yield
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            mount.engine.dispose()

    return create_app(
        settings.frontend_dist,
        session_factory=mount.session_factory,
        jwt_secret=settings.jwt_secret,
        access_token_hours=config.access_token_hours,
        clock=clock,
        agent_port=mount.agent_port,
        telemetry=telemetry,
        config=config,
        workspace=workspace(),
        policy=mount.policy,
        lifespan=lifespan,
    )

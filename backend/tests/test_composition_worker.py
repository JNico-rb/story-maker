"""El worker del montaje de `serve` (031-C02, C03): arranca con el servidor, toma la cola y se
apaga con él. El puerto de agente corre en su doble falso (003), la telemetría en el doble nulo
(001) o en el cliente de Langfuse simulado (004), y Lean en el doble del verificador formal: sin
modelo, sin Langfuse y sin GitHub (031-I2)."""

from __future__ import annotations

import asyncio
import datetime as dt
import io
import sys
import types
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, ClassVar

import pytest
from fastapi import FastAPI
from pypdf import PdfWriter
from sqlalchemy.orm import Session, sessionmaker
from tests.agents.test_sdk_options import NoHooks
from tests.conftest import FakeLangfuseClient
from tests.test_composition import (
    fake_adapters,
    init_database,
    make_settings,
    served_app,
)

from story_maker.agents.fake import Call, FakeAgent, Hang, Say, Script
from story_maker.agents.port import SessionRequest
from story_maker.agents.profiles import role_profile
from story_maker.agents.sdk import SdkAgent, provider_env
from story_maker.agents.usage import Usage
from story_maker.composition import Adapters, real_adapters
from story_maker.config import Config, load_config
from story_maker.formal.double import ProgrammedFormalVerifier
from story_maker.formal.result import INVARIANTS, ChronologyResult
from story_maker.observability.langfuse_adapter import LangfuseObservability
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Trace
from story_maker.observability.roles import ROLE_LABELS
from story_maker.pipeline.planning.plan import (
    Beat,
    OutlineChapterSubmission,
    PlanSubmission,
    StyleSheetSubmission,
    WorldSubmission,
)
from story_maker.pipeline.queue import enqueue_generation
from story_maker.settings import ROOT, Settings
from story_maker.store.models import Brief, Chapter, Novel, RoleSession, Run, User
from story_maker.store.session import make_engine, make_session_factory, unit_of_work

NOW = dt.datetime(2026, 9, 24, 12, 0)
USAGE = Usage(input_tokens=1000, output_tokens=500, cache_read_tokens=0, cache_write_tokens=0)
PROMPTS = ROOT / "backend" / "harness_workspace" / "prompts"
PRODUCTION_ROLES = ("planner", "writer", "editor", "judge")
CHAPTER_CRITERIA = ("fidelidad-canon", "cumple-beats", "personalizacion-natural", "prosa", "tono")
NOVEL_CRITERIA = (
    "continuidad",
    "coherencia-personajes",
    "arco-y-final",
    "ritmo",
    "tono",
    "personalizacion-natural",
    "no-cliche",
)
BRIEF = {
    "recipient": {"name": "Marta", "age": 40},
    "occasion": "birthday",
    "genre": "adventure",
    "tone": "tender",
    "length": "medium",
    "dedication": "Para Marta",
    "banned_asked": True,
}
# El nombre de la destinataria es siempre el elemento personal 1 (`domain.brief`).
RECIPIENT_NAME_ELEMENT = "1"
PASSED = ChronologyResult("passed", dict.fromkeys(INVARIANTS, True))


def plan() -> dict[str, Any]:
    beats = tuple(Beat(number=n, description=f"Beat {n}.") for n in range(1, 4))
    chapters = tuple(
        OutlineChapterSubmission(
            number=n,
            title=f"Capítulo {n}",
            arc_function="función en el arco",
            beats=beats,
            assigned_elements=(RECIPIENT_NAME_ELEMENT,) if n == 1 else (),
        )
        for n in range(1, 11)
    )
    submission = PlanSubmission(
        world=WorldSubmission(
            novum_description="Las máquinas aprendieron a soñar.",
            novum_scope="technological",
            novum_date=dt.date(2021, 5, 1),
            consequences=["Una.", "Dos."],
        ),
        chapters=chapters,
        style_sheet=StyleSheetSubmission(narrator="third", tense="past", default_treatment="tu"),
        title="El verano de Marta",
    )
    return submission.model_dump(mode="json")


def chapter_text() -> str:
    words = ["Marta", *["palabra"] * 1249]
    return "\n\n".join(" ".join(words[i : i + 50]) for i in range(0, len(words), 50))


def chapter_review() -> dict[str, Any]:
    return {
        "scores": [
            {"criterion": c, "score": 4, "justification": f"justificación de {c}"}
            for c in CHAPTER_CRITERIA
        ],
        "defects": [],
        "fact_usages": [],
        "events": [],
        "summary": "Resumen del capítulo.",
    }


def novel_evaluation() -> dict[str, Any]:
    return {
        c: {"score": 4, "justification": f"justificación de {c}", "chapters": [1]}
        for c in NOVEL_CRITERIA
    }


def script(*steps: Call) -> Script:
    return Script(steps=(*steps, Say("Fin.")), usage=USAGE, sdk_cost_usd=0.1)


def script_published_novel(fake: FakeAgent) -> None:
    """Un plan aceptado, diez capítulos aceptados al primer intento y un juez que aprueba."""
    fake.script("planner", "plan", script(Call("submit_plan", plan())))
    for _ in range(10):
        fake.script(
            "writer",
            "write",
            script(Call("submit_chapter", {"title": "El faro", "text": chapter_text()})),
        )
        fake.script("editor", None, script(Call("submit_review", chapter_review())))
    fake.script("judge", None, script(Call("submit_evaluation", novel_evaluation())))


def novel_pdf(html: str) -> bytes:
    """Doble del render: un PDF con el ancla de cada capítulo, que pasa `pdf-enlaces`."""
    del html
    writer = PdfWriter()
    for number in range(1, 11):
        writer.add_blank_page(width=200, height=200)
        writer.add_named_destination(f"/cap-{number}", number - 1)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


@pytest.fixture
def config() -> Config:
    return load_config(ROOT / "config.json")


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    path = tmp_path / "data"
    init_database(path)
    return path


@pytest.fixture
def session_factory(data_dir: Path) -> sessionmaker[Session]:
    return make_session_factory(make_engine(data_dir / "story-maker.db"))


def queue_generation(
    session_factory: sessionmaker[Session], config: Config, email: str = "cliente@example.com"
) -> int:
    with session_factory() as session:
        user = User(email=email, password_hash="x", created_at=NOW)
        session.add(user)
        session.flush()
        novel = Novel(
            user_id=user.id, title=None, embedding_model=config.embedding_model, created_at=NOW
        )
        session.add(novel)
        session.flush()
        session.add(Brief(novel_id=novel.id, content=BRIEF, status="confirmed"))
        session.commit()
        novel_id = novel.id
    with unit_of_work(session_factory) as uow:
        run_id, _ = enqueue_generation(uow, novel_id, now=NOW)
    return run_id


def status_of(session_factory: sessionmaker[Session], run_id: int) -> str:
    with session_factory() as session:
        return session.get_one(Run, run_id).status


async def until(condition: Callable[[], bool], seconds: float = 60) -> None:
    async with asyncio.timeout(seconds):
        while not condition():
            await asyncio.sleep(0.02)


async def serve_until(app: FastAPI, condition: Callable[[], bool]) -> None:
    """Arranca el servidor (su lifespan), espera a `condition` y lo para."""
    async with app.router.lifespan_context(app):
        await until(condition)


def app_with(
    settings: Settings, fake: FakeAgent, telemetry: NullObservability | LangfuseObservability
) -> FastAPI:
    adapters = fake_adapters(
        fake, verifier=ProgrammedFormalVerifier([PASSED]), render_pdf=novel_pdf
    )
    return served_app(settings, adapters, telemetry)


def finished(session_factory: sessionmaker[Session], run_id: int) -> Callable[[], bool]:
    return lambda: status_of(session_factory, run_id) not in ("queued", "running")


async def test_starting_the_server_takes_the_queued_generation_through_to_published(
    data_dir: Path,
    tmp_path: Path,
    session_factory: sessionmaker[Session],
    config: Config,
) -> None:
    run_id = queue_generation(session_factory, config)
    fake = FakeAgent()
    script_published_novel(fake)
    app = app_with(make_settings(data_dir, tmp_path / "sin-dist"), fake, NullObservability())

    await serve_until(app, finished(session_factory, run_id))

    with session_factory() as session:
        run = session.get_one(Run, run_id)
        assert (run.status, run.reason) == ("published", None)
        sessions = session.query(RoleSession).filter(RoleSession.run_id == run_id).all()
    assert {s.role for s in sessions} == set(PRODUCTION_ROLES)
    assert all(s.prompt_version is None for s in sessions)
    for opened in fake.sessions:
        role = opened.request.role
        assert opened.profile.model == config.roles[role].model
        assert opened.request.prompt == (PROMPTS / f"{role}.md").read_text(encoding="utf-8")


async def test_each_role_session_keeps_the_langfuse_version_of_its_prompt(
    data_dir: Path,
    tmp_path: Path,
    session_factory: sessionmaker[Session],
    config: Config,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_id = queue_generation(session_factory, config)
    client = FakeLangfuseClient()
    versions = {role: 10 + i for i, role in enumerate(PRODUCTION_ROLES)}
    for role, number in versions.items():
        client.register_prompt(ROLE_LABELS[role], "produccion", version=number)
    for name, value in {
        "LANGFUSE_PUBLIC_KEY": "pk-lf-TU_CLAVE_AQUI",
        "LANGFUSE_SECRET_KEY": "sk-lf-TU_CLAVE_AQUI",
        "LANGFUSE_BASE_URL": "http://127.0.0.1:3000",
        "LANGFUSE_PROMPT_LABEL": "produccion",
    }.items():
        monkeypatch.setenv(name, value)
    settings = make_settings(data_dir, tmp_path / "sin-dist", inherit_env=True)
    fake = FakeAgent()
    script_published_novel(fake)
    app = app_with(settings, fake, LangfuseObservability(client))

    await serve_until(app, finished(session_factory, run_id))

    with session_factory() as session:
        assert session.get_one(Run, run_id).status == "published"
        sessions = session.query(RoleSession).filter(RoleSession.run_id == run_id).all()
    assert {(s.role, s.prompt_version) for s in sessions} == {
        (role, str(number)) for role, number in versions.items()
    }


def test_the_agent_of_the_mount_is_the_one_of_llm_provider_with_the_role_profiles(
    data_dir: Path, tmp_path: Path, config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "anthropic_compatible")
    monkeypatch.setenv("OPENROUTER_API_KEY", "TU_CLAVE_AQUI")
    settings = make_settings(data_dir, tmp_path / "sin-dist", inherit_env=True)
    agent = real_adapters(settings, config).agent
    assert isinstance(agent, SdkAgent)
    request = SessionRequest(
        role="planner",
        mode="plan",
        user_id=1,
        novel_id=1,
        prompt="Prompt del planner",
        message="{}",
        tools=(),
        trace=Trace(key="run:1", name="generacion", session="1"),
    )

    options = agent.session_options(request, role_profile(config, "planner", "plan"), NoHooks())

    assert options.env == provider_env(settings)
    assert options.env["ANTHROPIC_AUTH_TOKEN"] == "TU_CLAVE_AQUI"
    assert options.model == config.roles["planner"].model


def writer_sessions(fake: FakeAgent) -> int:
    return sum(opened.request.role == "writer" for opened in fake.sessions)


async def test_stopping_the_server_stops_the_worker_without_losing_anything(
    data_dir: Path,
    tmp_path: Path,
    session_factory: sessionmaker[Session],
    config: Config,
) -> None:
    running_id = queue_generation(session_factory, config)
    queued_id = queue_generation(session_factory, config, email="otra@example.com")
    fake = FakeAgent()
    fake.script("planner", "plan", script(Call("submit_plan", plan())))
    fake.script(
        "writer",
        "write",
        script(Call("submit_chapter", {"title": "El faro", "text": chapter_text()})),
    )
    fake.script("editor", None, script(Call("submit_review", chapter_review())))
    fake.script("writer", "write", Script(steps=(Hang(),), usage=USAGE))
    settings = make_settings(data_dir, tmp_path / "sin-dist")

    await serve_until(
        app_with(settings, fake, NullObservability()), lambda: writer_sessions(fake) == 2
    )

    pending = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    assert pending == []
    open_session = fake.sessions[-1]
    assert (open_session.interrupted, open_session.disconnected) == (True, True)
    assert status_of(session_factory, running_id) == "running"
    assert status_of(session_factory, queued_id) == "queued"
    with session_factory() as session:
        assert [c.number for c in session.query(Chapter).all()] == [1]

    restarted = app_with(settings, FakeAgent(), NullObservability())
    await serve_until(restarted, lambda: status_of(session_factory, running_id) != "running")

    with session_factory() as session:
        run = session.get_one(Run, running_id)
        assert (run.status, run.reason) == ("interrupted", "crash")


class LocalTextEmbedding:
    """Doble de la clase de `fastembed`: apunta con qué modelo se carga y qué incrusta."""

    loaded: ClassVar[list[str]] = []
    embedded: ClassVar[list[str]] = []

    def __init__(self, model_name: str) -> None:
        self.loaded.append(model_name)

    def embed(self, documents: Iterable[str]) -> Iterable[list[float]]:
        texts = list(documents)
        self.embedded.extend(texts)
        return [[0.5, 0.5] for _ in texts]


async def test_a_new_novel_syncs_its_cards_with_the_local_embedding_model_of_the_mount(
    data_dir: Path,
    tmp_path: Path,
    session_factory: sessionmaker[Session],
    config: Config,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        sys.modules, "fastembed", types.SimpleNamespace(TextEmbedding=LocalTextEmbedding)
    )
    monkeypatch.setattr(LocalTextEmbedding, "loaded", [])
    monkeypatch.setattr(LocalTextEmbedding, "embedded", [])
    run_id = queue_generation(session_factory, config)
    with session_factory() as session:
        novel_model = session.get_one(Novel, session.get_one(Run, run_id).novel_id).embedding_model
    settings = make_settings(data_dir, tmp_path / "sin-dist")
    fake = FakeAgent()
    script_published_novel(fake)
    mounted = real_adapters(settings, config)
    adapters = Adapters(
        agent=fake,
        formal_verifier=ProgrammedFormalVerifier([PASSED]),
        render_pdf=novel_pdf,
        embedder=mounted.embedder,
    )

    await serve_until(served_app(settings, adapters), finished(session_factory, run_id))

    assert status_of(session_factory, run_id) == "published"
    assert LocalTextEmbedding.loaded == [novel_model]
    assert LocalTextEmbedding.embedded != []

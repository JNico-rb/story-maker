"""031-C06: `example` y `evals run` sirven la vista en `STORY_MAKER_BASE_URL` mientras el worker
del montaje procesa la cola; sin ello, la etapa 3 del gate (017) no puede navegarla."""

from __future__ import annotations

import json
import shutil
import socket
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import httpx
import pytest
from tests.test_cli_evals_run import REAL_ROOT, EvalAgent, _free_port, _register
from tests.test_composition_worker import PASSED, novel_pdf
from typer.testing import CliRunner

import story_maker.cli as cli_module
import story_maker.settings as settings_module
from story_maker.agents.fake import FakeSession
from story_maker.agents.port import SessionRequest, ToolHooks
from story_maker.agents.profiles import RoleProfile
from story_maker.cli import EVAL_BRIEFS_DIR, app
from story_maker.composition import Adapters
from story_maker.formal.double import ProgrammedFormalVerifier
from story_maker.pipeline.worker import Worker
from story_maker.retrieval.fake import FixedVectors
from story_maker.store import models
from story_maker.store.session import create_schema, make_engine, make_session_factory

runner = CliRunner()
EMAIL = "cliente@example.com"


@dataclass(frozen=True)
class Fetched:
    url: str
    status: int
    body: str


@dataclass
class ViewFetchingSession(FakeSession):
    """El revisor visual del doble: antes de entregar, pide la vista por HTTP a la dirección que
    le da el gate, como haría el navegador del revisor real."""

    fetched: list[Fetched] = field(default_factory=list)

    async def run(self) -> None:
        url = json.loads(self.request.message)["url"]
        async with httpx.AsyncClient(trust_env=False) as client:
            response = await client.get(url, timeout=10)
        self.fetched.append(Fetched(url, response.status_code, response.text))
        await super().run()


class ViewFetchingAgent(EvalAgent):
    def __init__(self, db_path: Path) -> None:
        super().__init__(db_path)
        self.fetched: list[Fetched] = []

    def open(self, request: SessionRequest, profile: RoleProfile, hooks: ToolHooks) -> FakeSession:
        if request.role != "visual_reviewer":
            return super().open(request, profile, hooks)
        session = ViewFetchingSession(
            request, profile, hooks, self._script(request), fetched=self.fetched
        )
        self.sessions.append(session)
        return session


@pytest.fixture
def port(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> int:
    """Raíz aislada con el `config.json` y el workspace del repositorio, la base creada con un
    cliente registrado y `STORY_MAKER_BASE_URL` en un puerto libre."""
    monkeypatch.setattr(settings_module, "ROOT", tmp_path)
    free = _free_port()
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("FORMAL_VERIFIER", "local")
    monkeypatch.setenv("STORY_MAKER_BASE_URL", f"http://127.0.0.1:{free}")
    monkeypatch.delenv("CI", raising=False)
    shutil.copy(REAL_ROOT / "config.json", tmp_path / "config.json")
    shutil.copytree(
        REAL_ROOT / "backend" / "harness_workspace", tmp_path / "backend" / "harness_workspace"
    )
    db_path = _db_path(tmp_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = make_engine(db_path)
    create_schema(engine)
    engine.dispose()
    _register(db_path, EMAIL)
    return free


def _db_path(root: Path) -> Path:
    return root / "backend" / "data" / "story-maker.db"


@pytest.fixture
def agent(port: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[EvalAgent]:
    del port
    double = ViewFetchingAgent(_db_path(tmp_path))
    adapters = Adapters(
        agent=double,
        formal_verifier=ProgrammedFormalVerifier([PASSED] * 10),
        render_pdf=novel_pdf,
        embedder=FixedVectors(),
    )
    monkeypatch.setattr(cli_module, "real_adapters", lambda settings, config: adapters)
    yield double
    double.dispose()


@pytest.fixture
def worker_loops(monkeypatch: pytest.MonkeyPatch) -> list[Worker]:
    """Cada `run_forever` que arranca: el worker de un lifespan de servidor, no el del montaje,
    que toma la cola con `run_next`."""
    started: list[Worker] = []
    original = Worker.run_forever

    async def recording(self: Worker) -> None:
        started.append(self)
        await original(self)

    monkeypatch.setattr(Worker, "run_forever", recording)
    return started


def _port_is_free(port: int) -> bool:
    try:
        socket.create_server(("127.0.0.1", port)).close()
    except OSError:
        return False
    return True


def _published(root: Path) -> dict[str, str | None]:
    """La ruta de la vista de cada versión publicada y el título de su novela."""
    engine = make_engine(_db_path(root))
    try:
        with make_session_factory(engine)() as session:
            versions = session.query(models.Version).filter_by(status="published").all()
            return {
                f"/view/versions/{v.id}": session.get_one(models.Novel, v.novel_id).title
                for v in versions
            }
    finally:
        engine.dispose()


def _invoke(command: str, tmp_path: Path) -> list[str]:
    if command == "example":
        brief = str(EVAL_BRIEFS_DIR / "01-ejemplo.json")
        return ["example", brief, "--email", EMAIL, "--out", str(tmp_path / "ejemplo.pdf")]
    return ["evals", "run", "--email", EMAIL]


@pytest.mark.parametrize("command", ["example", "evals run"])
def test_the_view_answers_at_the_base_url_while_the_queue_drains_and_the_port_is_freed_after(
    command: str,
    agent: ViewFetchingAgent,
    worker_loops: list[Worker],
    port: int,
    tmp_path: Path,
) -> None:
    result = runner.invoke(app, _invoke(command, tmp_path))

    assert result.exit_code == 0, result.stdout
    published = _published(tmp_path)
    assert published
    assert sorted(urlparse(f.url).path for f in agent.fetched) == sorted(published)
    for fetched in agent.fetched:
        assert urlparse(fetched.url).netloc == f"127.0.0.1:{port}"
        assert fetched.status == 200, fetched.body
        title = published[urlparse(fetched.url).path]
        assert title
        assert title in fetched.body
    assert worker_loops == []
    assert _port_is_free(port)


@pytest.mark.parametrize("command", ["example", "evals run"])
def test_with_the_base_url_port_taken_the_command_fails_naming_it_and_creates_nothing(
    command: str,
    agent: ViewFetchingAgent,
    port: int,
    tmp_path: Path,
) -> None:
    taken = socket.create_server(("127.0.0.1", port))
    try:
        result = runner.invoke(app, _invoke(command, tmp_path))
    finally:
        taken.close()

    assert result.exit_code != 0
    assert str(port) in result.stdout
    assert agent.sessions == []
    engine = make_engine(_db_path(tmp_path))
    try:
        with make_session_factory(engine)() as session:
            assert session.query(models.Novel).count() == 0
            assert session.query(models.Run).count() == 0
    finally:
        engine.dispose()

"""`story-maker evals run` (020-C02..C05), `example` (020-C15) y la validez de los briefs de
evals (020-C01)."""

from __future__ import annotations

import datetime as dt
import json
import shutil
import socket
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from tests.test_cli_evals import _row
from tests.test_composition_worker import (
    PASSED,
    chapter_review,
    novel_evaluation,
    novel_pdf,
    script,
)
from typer.testing import CliRunner

import story_maker.cli as cli_module
import story_maker.settings as settings_module
from story_maker.agents.fake import Call, FakeSession, Script
from story_maker.agents.port import SessionRequest, ToolHooks
from story_maker.agents.profiles import RoleProfile
from story_maker.cli import EVAL_BRIEF_SLUGS, EVAL_BRIEFS_DIR, EVAL_MAX_MANDATORY_ELEMENTS, app
from story_maker.cli import eval_brief_content as _eval_brief_content
from story_maker.composition import Adapters
from story_maker.config import load_config
from story_maker.domain.brief import BriefContent, brief_problems
from story_maker.formal.double import ProgrammedFormalVerifier
from story_maker.pipeline.planning.plan import (
    Beat,
    OutlineChapterSubmission,
    PlanSubmission,
    StyleSheetSubmission,
    WorldSubmission,
)
from story_maker.render.pdf_links import check_pdf_links
from story_maker.retrieval.fake import FixedVectors
from story_maker.store import models
from story_maker.store.session import create_schema, make_engine, make_session_factory

NOW = dt.datetime(2026, 9, 24, 11, 0)
CREATED_AT = NOW.date()
runner = CliRunner()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture
def isolated_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(settings_module, "ROOT", tmp_path)
    return tmp_path


@pytest.fixture
def base_env(monkeypatch: pytest.MonkeyPatch, isolated_root: Path) -> Path:
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("FORMAL_VERIFIER", "local")
    monkeypatch.setenv("STORY_MAKER_BASE_URL", f"http://127.0.0.1:{_free_port()}")
    monkeypatch.delenv("CI", raising=False)
    return isolated_root


def _db_path(base_env: Path) -> Path:
    return base_env / "backend" / "data" / "story-maker.db"


def _init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = make_engine(db_path)
    create_schema(engine)
    engine.dispose()


# --- 020-C01: los cinco briefs del repositorio son válidos ----------------------------------


def test_the_five_eval_briefs_are_schema_brief_valid_with_no_c1_to_c6_contradiction() -> None:
    """020-C01: exactamente cinco briefs, todos válidos; el adversarial lleva una instrucción
    dirigida al sistema en un texto libre, y el temporal un recuerdo con una partida definitiva
    (`excluded`) que un deseo de trama contradice."""
    files = sorted(EVAL_BRIEFS_DIR.glob("*.json"))

    assert len(files) == 5
    by_slug: dict[str, tuple[BriefContent, list[str]]] = {}
    slugs = []
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        slugs.append(data["name"])
        content, banned_entries, free_texts = _eval_brief_content(data)
        problems = brief_problems(
            content, CREATED_AT, banned_entries, [], EVAL_MAX_MANDATORY_ELEMENTS
        )
        assert problems == [], (path.name, problems)
        by_slug[data["name"]] = (content, free_texts)

    assert slugs == list(EVAL_BRIEF_SLUGS)

    _adversarial_content, adversarial_free_texts = by_slug["adversarial"]
    assert any("instrucciones" in text.lower() for text in adversarial_free_texts)

    temporal_content, _temporal_free_texts = by_slug["temporal"]
    excluded_names = {r.excluded for r in temporal_content.recollections if r.excluded}
    assert excluded_names
    assert any(
        excluded in wish.statement
        for excluded in excluded_names
        for wish in temporal_content.plot_wishes
    )


# --- 020-C02: sin un cliente registrado no se crea nada -------------------------------------


def test_evals_run_without_email_creates_nothing(base_env: Path) -> None:
    result = runner.invoke(app, ["evals", "run"])

    assert result.exit_code != 0
    assert result.stdout.strip() != ""


def test_evals_run_with_an_unregistered_email_creates_nothing(base_env: Path) -> None:
    db_path = _db_path(base_env)
    _init_db(db_path)

    result = runner.invoke(app, ["evals", "run", "--email", "nadie@example.com"])

    assert result.exit_code != 0
    assert "nadie@example.com" in result.stdout
    engine = make_engine(db_path)
    try:
        with make_session_factory(engine)() as session:
            assert session.query(models.Novel).count() == 0
            assert session.query(models.Brief).count() == 0
            assert session.query(models.Run).count() == 0
    finally:
        engine.dispose()


# --- 020-C05: `evals run` no corre en la CI ---------------------------------------------------


def test_evals_run_refuses_to_run_in_ci(base_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = _db_path(base_env)
    _init_db(db_path)
    user_email = "cliente@example.com"
    engine = make_engine(db_path)
    try:
        with make_session_factory(engine)() as session:
            session.add(models.User(email=user_email, password_hash="h", created_at=NOW))
            session.commit()
    finally:
        engine.dispose()
    monkeypatch.setenv("CI", "true")

    result = runner.invoke(app, ["evals", "run", "--email", user_email])

    assert result.exit_code != 0
    engine = make_engine(db_path)
    try:
        with make_session_factory(engine)() as session:
            assert session.query(models.Novel).count() == 0
    finally:
        engine.dispose()


# --- 020-C03: una novela y una ejecución por brief, del cliente dado --------------------------
#
# El doble falso guionizado para publicar (003) sigue el guion de `script_published_novel`, pero
# adaptado a la novela que abre cada sesión: el planner asigna al capítulo 1 los elementos
# obligatorios del brief de esa novela y el editor declara el uso de sus hechos. Así cualquiera
# de los cinco briefs llega a `published` sin tocar ningún validador.

REAL_ROOT = settings_module.ROOT
EJEMPLO_FACT_QUOTE = "Marta trabaja restaurando barcos de madera"


def _eval_plan(assigned: tuple[str, ...], title: str) -> dict[str, Any]:
    beats = tuple(Beat(number=n, description=f"Beat {n}.") for n in range(1, 4))
    chapters = tuple(
        OutlineChapterSubmission(
            number=n,
            title=f"Capítulo {n}",
            arc_function="función en el arco",
            beats=beats,
            assigned_elements=assigned if n == 1 else (),
        )
        for n in range(1, 11)
    )
    return PlanSubmission(
        world=WorldSubmission(
            novum_description="Las máquinas aprendieron a soñar.",
            novum_scope="technological",
            novum_date=dt.date(2021, 5, 1),
            consequences=["Una.", "Dos."],
        ),
        chapters=chapters,
        style_sheet=StyleSheetSubmission(narrator="third", tense="past", default_treatment="tu"),
        title=title,
    ).model_dump(mode="json")


def _eval_chapter_text() -> str:
    words = ["palabra"] * 1250
    return "\n\n".join(" ".join(words[i : i + 50]) for i in range(0, len(words), 50))


class EvalAgent:
    """Doble del puerto de agente para las evals: cada sesión sigue un guion que publica, hecho
    a la medida de la novela de la ejecución que la abre. Nunca llama a un modelo (020-I1)."""

    def __init__(self, db_path: Path) -> None:
        self._engine = make_engine(db_path)
        self._session_factory = make_session_factory(self._engine)
        self.sessions: list[FakeSession] = []

    def dispose(self) -> None:
        self._engine.dispose()

    def prepare(self, request: SessionRequest) -> None:
        del request

    def open(self, request: SessionRequest, profile: RoleProfile, hooks: ToolHooks) -> FakeSession:
        session = FakeSession(request, profile, hooks, self._script(request))
        self.sessions.append(session)
        return session

    def _mandatory_facts(self, run_id: int | None) -> list[models.Fact]:
        with self._session_factory() as session:
            run = session.get_one(models.Run, run_id)
            return list(
                session.query(models.Fact)
                .filter(
                    models.Fact.version_id == run.candidate_version_id,
                    models.Fact.mandatory.is_(True),
                    models.Fact.personal_element_id.is_not(None),
                )
                .order_by(models.Fact.id)
            )

    def _script(self, request: SessionRequest) -> Script:
        if request.role == "extractor":
            facts = []
            if EJEMPLO_FACT_QUOTE in request.message:
                facts.append(
                    {
                        "subject": "Marta",
                        "attribute": "oficio",
                        "value": "restaura barcos de madera",
                        "quote": EJEMPLO_FACT_QUOTE,
                    }
                )
            return script(Call("submit_facts", {"facts": facts}))
        if request.role == "planner":
            elements = tuple(
                sorted({str(f.personal_element_id) for f in self._mandatory_facts(request.run_id)})
            )
            plan = _eval_plan(elements, f"Novela {request.novel_id}")
            return script(Call("submit_plan", plan))
        if request.role == "writer":
            return script(
                Call("submit_chapter", {"title": "El faro", "text": _eval_chapter_text()})
            )
        if request.role == "editor":
            review = chapter_review()
            review["fact_usages"] = [f.id for f in self._mandatory_facts(request.run_id)]
            return script(Call("submit_review", review))
        if request.role == "judge":
            return script(Call("submit_evaluation", novel_evaluation()))
        raise AssertionError(f"sesión inesperada: {request.role} {request.mode}")


@pytest.fixture
def eval_env(base_env: Path) -> Path:
    """La raíz aislada con el `config.json` y el workspace de producto del repositorio."""
    shutil.copy(REAL_ROOT / "config.json", base_env / "config.json")
    shutil.copytree(
        REAL_ROOT / "backend" / "harness_workspace", base_env / "backend" / "harness_workspace"
    )
    return base_env


def _register(db_path: Path, email: str) -> int:
    engine = make_engine(db_path)
    try:
        with make_session_factory(engine)() as session:
            user = models.User(email=email, password_hash="h", created_at=NOW)
            session.add(user)
            session.commit()
            return user.id
    finally:
        engine.dispose()


@pytest.fixture
def eval_agent(
    eval_env: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[tuple[EvalAgent, ProgrammedFormalVerifier]]:
    db_path = _db_path(eval_env)
    _init_db(db_path)
    agent = EvalAgent(db_path)
    verifier = ProgrammedFormalVerifier([PASSED] * 10)
    adapters = Adapters(
        agent=agent, formal_verifier=verifier, render_pdf=novel_pdf, embedder=FixedVectors()
    )
    monkeypatch.setattr(cli_module, "real_adapters", lambda settings, config: adapters)
    yield agent, verifier
    agent.dispose()


def _brief_files() -> list[Path]:
    return sorted(EVAL_BRIEFS_DIR.glob("*.json"))


def test_evals_run_publishes_one_novel_and_one_run_per_brief_of_the_given_client(
    eval_env: Path, eval_agent: tuple[EvalAgent, ProgrammedFormalVerifier]
) -> None:
    db_path = _db_path(eval_env)
    user_id = _register(db_path, "cliente@example.com")
    _register(db_path, "otro@example.com")

    result = runner.invoke(app, ["evals", "run", "--email", "cliente@example.com"])

    assert result.exit_code == 0, result.stdout
    engine = make_engine(db_path)
    try:
        with make_session_factory(engine)() as session:
            novels = session.query(models.Novel).order_by(models.Novel.id).all()
            assert [n.eval_brief for n in novels] == list(EVAL_BRIEF_SLUGS)
            assert {n.user_id for n in novels} == {user_id}
            for novel, path in zip(novels, _brief_files(), strict=True):
                content, _banned, _free = _eval_brief_content(
                    json.loads(path.read_text(encoding="utf-8"))
                )
                brief = session.query(models.Brief).filter_by(novel_id=novel.id).one()
                assert (brief.status, brief.content) == (
                    "confirmed",
                    content.model_dump(mode="json"),
                )
                runs = session.query(models.Run).filter_by(novel_id=novel.id).all()
                assert [(r.type, r.status) for r in runs] == [("generation", "published")]
                assert f"{novel.eval_brief}: novela {novel.id}, ejecución {runs[0].id}" in (
                    result.stdout
                )
            facts = session.query(models.ExtractedFact).all()
            assert [(f.quote, f.accepted) for f in facts] == [(EJEMPLO_FACT_QUOTE, True)]
    finally:
        engine.dispose()

    table = runner.invoke(app, ["evals", "table"])

    assert table.exit_code == 0, table.stdout
    assert _row(table.stdout, "Estado final (`published`/`failed` + motivo)") == ["published"] * 5


# --- 020-C04: un brief que no pasa no para a los demás ---------------------------------------


def test_an_invalid_brief_creates_no_novel_and_the_other_four_still_publish(
    eval_env: Path,
    eval_agent: tuple[EvalAgent, ProgrammedFormalVerifier],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    briefs_dir = tmp_path / "briefs"
    briefs_dir.mkdir()
    for path in _brief_files():
        shutil.copy(path, briefs_dir / path.name)
    broken = briefs_dir / "02-infantil.json"
    data = json.loads(broken.read_text(encoding="utf-8"))
    data["brief"]["genre"] = "saga-espacial"
    broken.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(cli_module, "EVAL_BRIEFS_DIR", briefs_dir)
    db_path = _db_path(eval_env)
    _register(db_path, "cliente@example.com")

    result = runner.invoke(app, ["evals", "run", "--email", "cliente@example.com"])

    assert result.exit_code != 0
    defect = [line for line in result.stdout.splitlines() if line.startswith("infantil:")]
    assert len(defect) == 1
    assert "schema-brief" in defect[0]
    assert "genre" in defect[0]
    engine = make_engine(db_path)
    try:
        with make_session_factory(engine)() as session:
            novels = session.query(models.Novel).order_by(models.Novel.id).all()
            assert [n.eval_brief for n in novels] == ["ejemplo", "boda", "adversarial", "temporal"]
            assert session.query(models.Brief).count() == 4
            runs = session.query(models.Run).order_by(models.Run.id).all()
            assert [r.status for r in runs] == ["published"] * 4
    finally:
        engine.dispose()


# --- 020-C15: `example` produce la novela y su PDF -------------------------------------------


def test_example_publishes_a_novel_of_the_client_and_saves_its_pdf_at_the_given_path(
    eval_env: Path,
    eval_agent: tuple[EvalAgent, ProgrammedFormalVerifier],
    tmp_path: Path,
) -> None:
    db_path = _db_path(eval_env)
    user_id = _register(db_path, "cliente@example.com")
    out = tmp_path / "salida" / "novela-ejemplo.pdf"
    brief = EVAL_BRIEFS_DIR / "01-ejemplo.json"

    result = runner.invoke(
        app, ["example", str(brief), "--email", "cliente@example.com", "--out", str(out)]
    )

    assert result.exit_code == 0, result.stdout
    engine = make_engine(db_path)
    try:
        with make_session_factory(engine)() as session:
            novel = session.query(models.Novel).one()
            assert novel.user_id == user_id
            version = session.query(models.Version).filter_by(novel_id=novel.id).one()
            assert (version.status, version.number) == ("published", 1)
            assert version.pdf_path is not None
            stored = Path(version.pdf_path).read_bytes()
    finally:
        engine.dispose()
    assert out.read_bytes() == stored
    assert check_pdf_links(out.read_bytes()).passed
    assert str(out) in result.stdout


# --- 020-C17: un brief que ya tiene novela del cliente no se repite --------------------------


def test_evals_run_counts_the_example_novel_as_the_one_of_its_brief(
    eval_env: Path, eval_agent: tuple[EvalAgent, ProgrammedFormalVerifier], tmp_path: Path
) -> None:
    db_path = _db_path(eval_env)
    _register(db_path, "cliente@example.com")
    example = runner.invoke(
        app,
        [
            "example",
            str(EVAL_BRIEFS_DIR / "01-ejemplo.json"),
            "--email",
            "cliente@example.com",
            "--out",
            str(tmp_path / "novela-ejemplo.pdf"),
        ],
    )
    assert example.exit_code == 0, example.stdout
    engine = make_engine(db_path)
    try:
        with make_session_factory(engine)() as session:
            example_novel = session.query(models.Novel).one()
            example_run = session.query(models.Run).one()
            assert example_novel.eval_brief == "ejemplo"
            example_ids = (example_novel.id, example_run.id)
    finally:
        engine.dispose()

    result = runner.invoke(app, ["evals", "run", "--email", "cliente@example.com"])

    assert result.exit_code == 0, result.stdout
    assert f"ejemplo: novela {example_ids[0]}, ejecución {example_ids[1]} (published)" in (
        result.stdout
    )
    engine = make_engine(db_path)
    try:
        with make_session_factory(engine)() as session:
            novels = session.query(models.Novel).order_by(models.Novel.id).all()
            assert [n.eval_brief for n in novels] == list(EVAL_BRIEF_SLUGS)
            assert novels[0].id == example_ids[0]
            runs = session.query(models.Run).order_by(models.Run.id).all()
            assert [r.status for r in runs] == ["published"] * 5
    finally:
        engine.dispose()
    table = runner.invoke(app, ["evals", "table"])
    assert _row(table.stdout, "Estado final (`published`/`failed` + motivo)") == ["published"] * 5


def _seed_eval_novel(
    db_path: Path, user_id: int, path: Path, *, run_status: str
) -> tuple[int, int]:
    """Una novela de un `evals run` anterior, con su brief confirmado y su ejecución de
    generación sin terminar."""
    content, _banned, _free = _eval_brief_content(json.loads(path.read_text(encoding="utf-8")))
    engine = make_engine(db_path)
    try:
        with make_session_factory(engine)() as session:
            novel = models.Novel(
                user_id=user_id,
                title=None,
                embedding_model=load_config(REAL_ROOT / "config.json").embedding_model,
                created_at=NOW,
                eval_brief=path.stem.split("-", 1)[1],
            )
            session.add(novel)
            session.flush()
            session.add(
                models.Brief(
                    novel_id=novel.id, content=content.model_dump(mode="json"), status="confirmed"
                )
            )
            run = models.Run(
                novel_id=novel.id,
                type="generation",
                status=run_status,
                phase=None,
                chapter=None,
                resumes=0,
                reason="crash" if run_status == "interrupted" else None,
                created_at=NOW,
            )
            session.add(run)
            session.commit()
            return novel.id, run.id
    finally:
        engine.dispose()


def test_evals_run_takes_a_queued_or_interrupted_eval_run_to_published_without_relaunching_it(
    eval_env: Path, eval_agent: tuple[EvalAgent, ProgrammedFormalVerifier]
) -> None:
    db_path = _db_path(eval_env)
    user_id = _register(db_path, "cliente@example.com")
    files = _brief_files()
    queued = _seed_eval_novel(db_path, user_id, files[0], run_status="queued")
    interrupted = _seed_eval_novel(db_path, user_id, files[1], run_status="interrupted")

    result = runner.invoke(app, ["evals", "run", "--email", "cliente@example.com"])

    assert result.exit_code == 0, result.stdout
    assert f"ejemplo: novela {queued[0]}, ejecución {queued[1]} (published)" in result.stdout
    assert f"infantil: novela {interrupted[0]}, ejecución {interrupted[1]} (published)" in (
        result.stdout
    )
    engine = make_engine(db_path)
    try:
        with make_session_factory(engine)() as session:
            novels = session.query(models.Novel).order_by(models.Novel.id).all()
            assert [n.eval_brief for n in novels] == list(EVAL_BRIEF_SLUGS)
            runs = session.query(models.Run).order_by(models.Run.id).all()
            assert [(r.novel_id, r.status) for r in runs] == [(n.id, "published") for n in novels]
            assert session.get_one(models.Run, interrupted[1]).resumes == 1
    finally:
        engine.dispose()

"""`story-maker evals table` (020-C06, 020-C07, 020-C08, 020-C09, 020-I2)."""

from __future__ import annotations

import datetime as dt
import socket
from pathlib import Path

import pytest
from typer.testing import CliRunner

import story_maker.settings as settings_module
from story_maker.cli import app
from story_maker.store import models
from story_maker.store.session import create_schema, make_engine, make_session_factory, unit_of_work

NOW = dt.datetime(2026, 9, 24, 11, 0)
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
    return isolated_root


def _data_dir(base_env: Path) -> Path:
    return base_env / "backend" / "data"


def _db_path(base_env: Path) -> Path:
    return _data_dir(base_env) / "story-maker.db"


def _row(output: str, label: str) -> list[str]:
    for line in output.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] == label:
            return cells[1:]
    raise AssertionError(f"fila {label!r} no está en:\n{output}")


class _Seed:
    """Construye una base de fixture con las cinco novelas de evals y sus datos."""

    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = make_engine(db_path)
        create_schema(self.engine)
        self.session_factory = make_session_factory(self.engine)
        with unit_of_work(self.session_factory) as uow:
            user = models.User(email="evals@example.com", password_hash="h", created_at=NOW)
            uow.add(user)
            uow.session.flush()
            self.user_id = user.id
        self.novels: dict[str, int] = {}
        self.runs: dict[str, int] = {}

    def novel(self, slug: str) -> int:
        with unit_of_work(self.session_factory) as uow:
            novel = models.Novel(
                user_id=self.user_id,
                title=f"El título que el plan dio a {slug}",
                embedding_model="m1",
                created_at=NOW,
                eval_brief=slug,
            )
            uow.add(novel)
            uow.session.flush()
            self.novels[slug] = novel.id
        return novel.id

    def run(self, slug: str, *, status: str, reason: str | None = None) -> int:
        novel_id = self.novels[slug]
        with unit_of_work(self.session_factory) as uow:
            run = models.Run(
                novel_id=novel_id,
                type="generation",
                status=status,
                phase=None,
                chapter=None,
                base_version_id=None,
                candidate_version_id=None,
                resumes=0,
                reason=reason,
                reason_detail=None,
                created_at=NOW,
                finished_at=NOW,
            )
            uow.add(run)
            uow.session.flush()
            self.runs[slug] = run.id
        return run.id

    def version(self, novel_slug: str) -> int:
        with unit_of_work(self.session_factory) as uow:
            version = models.Version(
                novel_id=self.novels[novel_slug],
                status="candidate",
                number=None,
                base_version_id=None,
                changed_chapters=[],
                pdf_path=None,
                created_at=NOW,
                published_at=None,
            )
            uow.add(version)
            uow.session.flush()
            return version.id

    def validator_result(
        self,
        slug: str,
        version_id: int,
        validator: str,
        *,
        passed: bool,
        score: float | None = None,
        detail: object = None,
    ) -> None:
        with unit_of_work(self.session_factory) as uow:
            uow.add(
                models.ValidatorResult(
                    run_id=self.runs[slug],
                    version_id=version_id,
                    validator=validator,
                    chapter=None,
                    passed=passed,
                    score=score,
                    detail=detail if detail is not None else [],
                    created_at=NOW,
                )
            )

    def audit(self, slug: str, *, origin: str, decision: str) -> None:
        with unit_of_work(self.session_factory) as uow:
            uow.add(
                models.AuditLog(
                    user_id=self.user_id,
                    novel_id=self.novels[slug],
                    run_id=None,
                    role=None,
                    tool=None,
                    origin=origin,
                    decision=decision,
                    rule="r1",
                    detail=[],
                    created_at=NOW,
                )
            )

    def attempt(self, slug: str, *, evaluable: str, number: int, outcome: str | None) -> None:
        with unit_of_work(self.session_factory) as uow:
            uow.add(
                models.Attempt(
                    run_id=self.runs[slug],
                    change_request_id=None,
                    evaluable=evaluable,
                    chapter=None,
                    gate_cycle=None,
                    number=number,
                    outcome=outcome,
                )
            )

    def role_session(
        self,
        slug: str,
        *,
        input_tokens: int,
        output_tokens: int,
        reserved_tokens: int,
        cost_usd: float,
        latency_ms: int,
        prompt_version: str | None = "v3",
        trace_id: str | None = "trace-1",
    ) -> None:
        with unit_of_work(self.session_factory) as uow:
            uow.add(
                models.RoleSession(
                    novel_id=self.novels[slug],
                    run_id=self.runs[slug],
                    role="writer",
                    chapter=1,
                    model="m1",
                    prompt_version=prompt_version,
                    reserved_tokens=reserved_tokens,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cache_read_tokens=None,
                    cache_write_tokens=None,
                    cost_usd=cost_usd,
                    sdk_cost_usd=cost_usd,
                    latency_ms=latency_ms,
                    outcome="completed",
                    trace_id=trace_id,
                )
            )

    def dispose(self) -> None:
        self.engine.dispose()


def _seed_all_five(db_path: Path) -> _Seed:
    seed = _Seed(db_path)
    for slug in ("ejemplo", "infantil", "boda", "adversarial", "temporal"):
        seed.novel(slug)
    return seed


# --- 020-C06: celdas de la tabla brief x validador -----------------------------------------------


def test_evals_table_cell_legend_for_each_validator_situation(base_env: Path) -> None:
    db_path = _db_path(base_env)
    seed = _seed_all_five(db_path)

    seed.run("ejemplo", status="published")
    version_ejemplo = seed.version("ejemplo")
    # bloqueante por capítulo, pasa al final, 2 intentos rechazados por él
    seed.validator_result("ejemplo", version_ejemplo, "`schema-salida`", passed=False)
    seed.validator_result("ejemplo", version_ejemplo, "`schema-salida`", passed=False)
    seed.validator_result("ejemplo", version_ejemplo, "`schema-salida`", passed=True)
    # semántico con criterios 4, 3 y 5
    seed.validator_result(
        "ejemplo", version_ejemplo, "`rubrica-capitulo`", passed=True, detail=[4, 3, 5]
    )
    # linter con 7 avisos
    seed.validator_result("ejemplo", version_ejemplo, "`linter-repeticion`", passed=True, score=7)
    # `cronologia-lean` no llegó a ejecutarse: sin filas

    seed.run("boda", status="failed", reason="retries_exhausted")
    version_boda = seed.version("boda")
    # bloqueante por capítulo, la ejecución terminó `failed` por él, 3 rechazos
    seed.validator_result("boda", version_boda, "`outline`", passed=False)
    seed.validator_result("boda", version_boda, "`outline`", passed=False)
    seed.validator_result("boda", version_boda, "`outline`", passed=False)

    # detector de inyección con 2 marcas en `audit_log`
    seed.audit("adversarial", origin="free_text", decision="flag")
    seed.audit("adversarial", origin="free_text", decision="flag")

    # hook de política con 1 denegación en `audit_log`
    seed.audit("temporal", origin="policy_hook", decision="deny")

    result = runner.invoke(app, ["evals", "table"])
    seed.dispose()

    assert result.exit_code == 0, result.stdout
    row = _row(result.stdout, "`schema-salida`")
    assert row[0] == "pasa · 2"

    row = _row(result.stdout, "`outline`")
    assert row[2] == "falla · 3"

    row = _row(result.stdout, "`rubrica-capitulo`")
    assert row[0] == "4.0 (3)"

    row = _row(result.stdout, "`linter-repeticion`")
    assert row[0] == "7"

    row = _row(result.stdout, "`cronologia-lean`")
    assert row[0] == "n/a"

    row = _row(result.stdout, "Detector de inyección (flags en `audit_log`)")
    assert row[3] == "2"

    row = _row(result.stdout, "Hook de policy (denegaciones en `audit_log`)")
    assert row[4] == "1"


# --- 020-C07: resumen por brief ------------------------------------------------------------------


def test_evals_table_summary_computes_per_brief_metrics_and_first_session_trace_id(
    base_env: Path,
) -> None:
    db_path = _db_path(base_env)
    seed = _seed_all_five(db_path)

    seed.run("ejemplo", status="published")
    seed.attempt("ejemplo", evaluable="chapter", number=1, outcome="accept")
    seed.attempt("ejemplo", evaluable="chapter", number=1, outcome="rewrite")
    seed.attempt("ejemplo", evaluable="gate_cycle", number=1, outcome="accept")
    seed.role_session(
        "ejemplo",
        input_tokens=1000,
        output_tokens=200,
        reserved_tokens=5000,
        cost_usd=0.5,
        latency_ms=1200,
        prompt_version="v3",
        trace_id="trace-primera",
    )
    # varias sesiones de rol en la misma ejecución: la traza que se lista es la de la primera
    # (por orden de creación), no la última ni todas.
    seed.role_session(
        "ejemplo",
        input_tokens=500,
        output_tokens=100,
        reserved_tokens=3000,
        cost_usd=0.25,
        latency_ms=800,
        prompt_version="v3",
        trace_id="trace-segunda",
    )

    # sin ninguna sesión de rol: la traza es «—», no una cadena vacía ni un error.
    seed.run("boda", status="failed", reason="retries_exhausted")

    result = runner.invoke(app, ["evals", "table"])
    seed.dispose()

    assert result.exit_code == 0, result.stdout

    row = _row(result.stdout, "Estado final (`published`/`failed` + motivo)")
    assert row[0] == "published"
    assert row[2] == "failed (retries_exhausted)"

    row = _row(result.stdout, "Capítulos aceptados al primer intento")
    assert row[0] == "1"

    row = _row(result.stdout, "Ciclos de gate")
    assert row[0] == "1"

    row = _row(result.stdout, "Tokens (entrada / salida)")
    assert row[0] == "1500 / 300"

    row = _row(result.stdout, "Coste USD (Langfuse)")
    assert row[0] == "0.7500"

    row = _row(result.stdout, "Latencia total")
    assert row[0] == "2000 ms"

    row = _row(result.stdout, "Pico de tokens concurrentes reservados")
    assert row[0] == "5000"

    row = _row(result.stdout, "Etiqueta de prompts y commit")
    assert row[0].startswith("v3 · ")

    row = _row(result.stdout, "Identificador de traza")
    assert row[0] == "trace-primera"
    assert row[2] == "—"


# --- 020-C08: la tabla sale solo de SQLite --------------------------------------------------------


def test_evals_table_does_not_touch_langfuse_and_works_with_the_null_double(
    base_env: Path,
) -> None:
    """El doble nulo de observabilidad y la red saliente ya bloqueada (`conftest.py`, 001-I3)
    no impiden `evals table`: no lee nada externo (020-C08)."""
    db_path = _db_path(base_env)
    seed = _seed_all_five(db_path)
    seed.run("ejemplo", status="published")
    seed.dispose()

    first = runner.invoke(app, ["evals", "table"])
    assert first.exit_code == 0, first.stdout


# --- 020-C09: sin ejecuciones de evals, la tabla lo dice ------------------------------------------


def test_evals_table_without_eval_runs_asks_to_run_evals_first(base_env: Path) -> None:
    db_path = _db_path(base_env)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = make_engine(db_path)
    create_schema(engine)
    engine.dispose()

    result = runner.invoke(app, ["evals", "table"])

    assert result.exit_code != 0
    assert "evals run" in result.stdout


# --- 020-I2: `evals table` es determinista --------------------------------------------------------


def test_evals_table_is_deterministic_byte_for_byte(base_env: Path) -> None:
    db_path = _db_path(base_env)
    seed = _seed_all_five(db_path)
    seed.run("ejemplo", status="published")
    version_ejemplo = seed.version("ejemplo")
    seed.validator_result(
        "ejemplo", version_ejemplo, "`rubrica-capitulo`", passed=True, detail=[4, 5]
    )
    seed.dispose()

    first = runner.invoke(app, ["evals", "table"])
    second = runner.invoke(app, ["evals", "table"])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert first.stdout == second.stdout

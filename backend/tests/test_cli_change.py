"""`story-maker change` (029-C09 a C14, I1-I3): el cambio del lector de la 014 por terminal, en
el mismo proceso, con el doble falso del puerto de agente y el nulo de observabilidad."""

from __future__ import annotations

import datetime as dt
import hashlib
import itertools
import json
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

import story_maker.settings as settings_module
from story_maker.agents.fake import Call, Fail, FakeAgent, Script
from story_maker.cli import app
from story_maker.domain.banned_terms import normalize_token
from story_maker.store.brief_canon import (
    BriefCloseOne,
    BriefRecipient,
    ConfirmedBrief,
    create_generation_candidate,
)
from story_maker.store.models import (
    BannedTerm,
    Brief,
    ChangeRequest,
    Chapter,
    Character,
    Fact,
    FactUsage,
    Novel,
    Run,
    User,
)
from story_maker.store.session import make_engine, make_session_factory, unit_of_work
from story_maker.store.versions import publish

REAL_ROOT = settings_module.ROOT
REAL_CONFIG = json.loads((REAL_ROOT / "config.json").read_text(encoding="utf-8"))
EMAIL_A = "cliente-a@example.com"
EMAIL_B = "cliente-b@example.com"
NOW = dt.datetime(2026, 9, 24, 12, 0, 0)

runner = CliRunner()
_emails = itertools.count(1)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture
def isolated_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(settings_module, "ROOT", tmp_path)
    (tmp_path / "config.json").write_text(json.dumps(REAL_CONFIG), encoding="utf-8")
    workspace = tmp_path / "backend" / "harness_workspace"
    (workspace / "prompts").mkdir(parents=True)
    (workspace / "CLAUDE.md").write_text("Escribe en español.", encoding="utf-8")
    (workspace / "prompts" / "planner-change.md").write_text(
        "Eres el planner en modo cambio.", encoding="utf-8"
    )
    return tmp_path


@pytest.fixture
def base_env(monkeypatch: pytest.MonkeyPatch, isolated_root: Path) -> Path:
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("FORMAL_VERIFIER", "local")
    monkeypatch.setenv("STORY_MAKER_BASE_URL", f"http://127.0.0.1:{_free_port()}")
    return isolated_root


@pytest.fixture
def db_path(base_env: Path) -> Path:
    result = runner.invoke(app, ["init-db"])
    assert result.exit_code == 0
    return base_env / "backend" / "data" / "story-maker.db"


@dataclass(frozen=True)
class F:
    novel_id: int
    user_a: int
    user_b: int
    email_a: str
    email_b: str
    v1_id: int
    toby_name_fact: int
    toby_character: int


def _session_factory(db_path: Path):  # type: ignore[no-untyped-def]
    engine = make_engine(db_path)
    return make_session_factory(engine), engine


def build_f(db_path: Path) -> F:
    """Novela del cliente A con v1 publicada: hecho de nombre del perro Toby, usado en el
    capítulo 2, y tres capítulos con la misma frase literal para un fragmento."""
    email_a = f"{next(_emails)}-{EMAIL_A}"
    email_b = f"{next(_emails)}-{EMAIL_B}"
    session_factory, engine = _session_factory(db_path)
    try:
        with unit_of_work(session_factory) as uow:
            user_a = User(email=email_a, password_hash="h", created_at=NOW)
            user_b = User(email=email_b, password_hash="h", created_at=NOW)
            uow.add(user_a)
            uow.add(user_b)
            uow.session.flush()
            novel = Novel(
                user_id=user_a.id, title="La aventura de Ada", embedding_model="M1", created_at=NOW
            )
            uow.add(novel)
            uow.session.flush()
            uow.add(Brief(novel_id=novel.id, content={}, status="confirmed"))
            uow.add(
                BannedTerm(
                    level="global",
                    term="zoquete",
                    type="word",
                    keywords=None,
                    normalized=normalize_token("zoquete"),
                )
            )
            novel_id, a_id, b_id = novel.id, user_a.id, user_b.id

        brief = ConfirmedBrief(
            recipient=BriefRecipient("Ada", 30, name_element_id=1, traits=()),
            close_ones=(BriefCloseOne("Toby", "perro", "animal", element_id=2, mandatory=True),),
        )
        with unit_of_work(session_factory) as uow:
            v1_id = create_generation_candidate(uow, novel_id, brief, now=NOW).id

        with unit_of_work(session_factory) as uow:
            session = uow.session
            toby = session.query(Character).filter_by(version_id=v1_id, canonical_name="Toby").one()
            toby_name = (
                session.query(Fact)
                .filter_by(version_id=v1_id, character_id=toby.id, attribute="name")
                .one()
            )
            uow.add(FactUsage(fact_id=toby_name.id, chapter=2))
            for n in (1, 2, 3):
                text = "Ada camina por la ciudad."
                if n == 2:
                    text += " Toby ladra a su lado."
                uow.add(
                    Chapter(
                        version_id=v1_id,
                        number=n,
                        title=f"Capítulo {n}",
                        text=text,
                        summary=f"Resumen {n}",
                        word_count=100,
                        content_hash=hashlib.sha256(f"{n}-{text}".encode()).hexdigest(),
                    )
                )
            toby_name_id = toby_name.id
            toby_character_id = toby.id

        with unit_of_work(session_factory) as uow:
            publish(uow, v1_id, pdf_path="v1.pdf", now=NOW)
    finally:
        engine.dispose()

    return F(novel_id, a_id, b_id, email_a, email_b, v1_id, toby_name_id, toby_character_id)


def rename(fact_id: int, value: str) -> dict[str, Any]:
    return {"changes": [{"fact_id": fact_id, "new_value": value}]}


def new_trait(character_id: int, value: str) -> dict[str, Any]:
    return {
        "new_fact": {
            "subject_type": "character",
            "subject_id": character_id,
            "attribute": "trait",
            "value": value,
        }
    }


def propose(fake: FakeAgent, *proposals: dict[str, Any]) -> None:
    for proposal in proposals:
        fake.script("planner", "change", Script(steps=(Call("propose_change", proposal),)))


@pytest.fixture
def fake_agent(monkeypatch: pytest.MonkeyPatch) -> FakeAgent:
    import story_maker.cli as cli_module

    fake = FakeAgent()
    monkeypatch.setattr(cli_module, "_build_agent", lambda settings, workspace: fake)
    return fake


@pytest.fixture
def f(db_path: Path) -> F:
    return build_f(db_path)


def _change_requests(db_path: Path) -> list[ChangeRequest]:
    session_factory, engine = _session_factory(db_path)
    try:
        with session_factory() as session:
            return list(session.query(ChangeRequest).all())
    finally:
        engine.dispose()


def _runs(db_path: Path) -> list[Run]:
    session_factory, engine = _session_factory(db_path)
    try:
        with session_factory() as session:
            return list(session.query(Run).all())
    finally:
        engine.dispose()


REQUEST = "el perro se llama Nala"


# --- 029-C09: pedir un cambio sobre un hecho y confirmarlo -------------------------------------


def test_request_a_change_on_a_fact_and_confirm_it(
    db_path: Path, f: F, fake_agent: FakeAgent
) -> None:
    propose(fake_agent, rename(f.toby_name_fact, "Nala"))

    result = runner.invoke(
        app,
        [
            "change",
            str(f.novel_id),
            str(REQUEST),
            "--email",
            f.email_a,
            "--fact",
            str(f.toby_name_fact),
        ],
        input="s\n",
    )

    assert result.exit_code == 0, result.stdout
    assert f"hecho {f.toby_name_fact}: Toby → Nala" in result.stdout
    assert "capítulos afectados: 2" in result.stdout
    assert "¿Confirmar el cambio? [s/N]" in result.stdout
    assert "versión base 1" in result.stdout

    (row,) = _change_requests(db_path)
    assert row.status == "confirmed"
    assert row.run_id is not None
    (run,) = _runs(db_path)
    assert (run.id, run.type, run.status, run.base_version_id) == (
        row.run_id,
        "change_request",
        "queued",
        f.v1_id,
    )


# --- 029-C10: pedir un cambio sobre un fragmento ------------------------------------------------


def test_request_a_change_on_a_fragment_includes_its_chapter_among_the_affected(
    db_path: Path, f: F, fake_agent: FakeAgent
) -> None:
    propose(fake_agent, new_trait(f.toby_character, "teme las tormentas"))

    result = runner.invoke(
        app,
        [
            "change",
            str(f.novel_id),
            "el perro teme las tormentas",
            "--email",
            f.email_a,
            "--chapter",
            "3",
            "--fragment",
            "Ada camina por la ciudad.",
        ],
        input="n\n",
    )

    assert result.exit_code == 0, result.stdout
    assert "hecho nuevo: character" in result.stdout
    assert "capítulos afectados: 3" in result.stdout


# --- 029-C11: sin un sí, nada se encola ----------------------------------------------------------


@pytest.mark.parametrize("answer", ["n\n", "\n", ""])
def test_without_an_explicit_yes_nothing_is_queued(
    db_path: Path, f: F, fake_agent: FakeAgent, answer: str
) -> None:
    propose(fake_agent, rename(f.toby_name_fact, "Nala"))

    result = runner.invoke(
        app,
        [
            "change",
            str(f.novel_id),
            str(REQUEST),
            "--email",
            f.email_a,
            "--fact",
            str(f.toby_name_fact),
        ],
        input=answer,
    )

    assert result.exit_code == 0, result.stdout
    assert "el cambio no se ha confirmado" in result.stdout
    (row,) = _change_requests(db_path)
    assert row.status == "proposed"
    assert _runs(db_path) == []


# --- 029-C12: petición denegada o rechazada -------------------------------------------------------


def test_a_banned_request_exits_with_1_and_asks_nothing(
    db_path: Path, f: F, fake_agent: FakeAgent
) -> None:
    result = runner.invoke(
        app,
        [
            "change",
            str(f.novel_id),
            "que el perro se llame Zoquete",
            "--email",
            f.email_a,
            "--fact",
            str(f.toby_name_fact),
        ],
        input="s\n",
    )

    assert result.exit_code == 1, result.stdout
    assert "¿Confirmar el cambio?" not in result.stdout
    (row,) = _change_requests(db_path)
    assert row.status == "rejected"
    assert _runs(db_path) == []


def test_attempts_exhausted_exits_with_1_and_asks_nothing(
    db_path: Path, f: F, fake_agent: FakeAgent
) -> None:
    unchanged = rename(f.toby_name_fact, "Toby")
    fake_agent.script("planner", "change", Script(steps=(Call("propose_change", unchanged),)))
    fake_agent.script("planner", "change", Script(steps=(Call("propose_change", unchanged),)))
    fake_agent.script("planner", "change", Script(steps=(Call("propose_change", unchanged),)))

    result = runner.invoke(
        app,
        [
            "change",
            str(f.novel_id),
            str(REQUEST),
            "--email",
            f.email_a,
            "--fact",
            str(f.toby_name_fact),
        ],
        input="s\n",
    )

    assert result.exit_code == 1, result.stdout
    assert "¿Confirmar el cambio?" not in result.stdout
    (row,) = _change_requests(db_path)
    assert row.status == "rejected"
    assert _runs(db_path) == []


# --- 029-C13: sin proveedor o sin sitio en el techo -----------------------------------------------


def test_a_provider_failure_exits_with_2_and_leaves_no_request(
    db_path: Path, f: F, fake_agent: FakeAgent
) -> None:
    fake_agent.script("planner", "change", Script(steps=(Fail(),)))

    result = runner.invoke(
        app,
        [
            "change",
            str(f.novel_id),
            str(REQUEST),
            "--email",
            f.email_a,
            "--fact",
            str(f.toby_name_fact),
        ],
        input="s\n",
    )

    assert result.exit_code == 2, result.stdout
    assert "repítelo más tarde" in result.stdout
    assert _change_requests(db_path) == []


# --- 029-C14: novela ajena, inexistente o sin versión publicada ----------------------------------


def test_a_novel_of_another_client_exits_with_1_and_nothing_is_saved(
    db_path: Path, f: F, fake_agent: FakeAgent
) -> None:
    result = runner.invoke(
        app,
        [
            "change",
            str(f.novel_id),
            str(REQUEST),
            "--email",
            f.email_b,
            "--fact",
            str(f.toby_name_fact),
        ],
        input="s\n",
    )

    assert result.exit_code == 1, result.stdout
    assert "novela no encontrada" in result.stdout
    assert _change_requests(db_path) == []


def test_a_missing_novel_exits_with_1_and_nothing_is_saved(
    db_path: Path, f: F, fake_agent: FakeAgent
) -> None:
    result = runner.invoke(
        app,
        [
            "change",
            "999999",
            str(REQUEST),
            "--email",
            f.email_a,
            "--fact",
            str(f.toby_name_fact),
        ],
        input="s\n",
    )

    assert result.exit_code == 1, result.stdout
    assert "novela no encontrada" in result.stdout
    assert _change_requests(db_path) == []


def test_a_novel_without_a_published_version_exits_with_1(
    db_path: Path, fake_agent: FakeAgent
) -> None:
    session_factory, engine = _session_factory(db_path)
    try:
        with unit_of_work(session_factory) as uow:
            user = User(email="sin-publicar@example.com", password_hash="h", created_at=NOW)
            uow.add(user)
            uow.session.flush()
            novel = Novel(user_id=user.id, title=None, embedding_model="M1", created_at=NOW)
            uow.add(novel)
            uow.session.flush()
            uow.add(Brief(novel_id=novel.id, content={}, status="draft"))
            novel_id = novel.id
    finally:
        engine.dispose()

    result = runner.invoke(
        app,
        [
            "change",
            str(novel_id),
            str(REQUEST),
            "--email",
            "sin-publicar@example.com",
            "--fact",
            "1",
        ],
        input="s\n",
    )

    assert result.exit_code == 1, result.stdout
    assert "novela no encontrada" not in result.stdout
    assert _change_requests(db_path) == []


def test_a_fact_not_in_the_current_version_exits_with_1(
    db_path: Path, f: F, fake_agent: FakeAgent
) -> None:
    result = runner.invoke(
        app,
        [
            "change",
            str(f.novel_id),
            str(REQUEST),
            "--email",
            f.email_a,
            "--fact",
            "999999",
        ],
        input="s\n",
    )

    assert result.exit_code == 1, result.stdout
    assert "novela no encontrada" not in result.stdout
    assert _change_requests(db_path) == []

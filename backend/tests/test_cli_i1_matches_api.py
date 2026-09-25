"""029-I1 — la CLI decide como la API: el mismo guion (un turno, un texto libre, la confirmación
del brief, y una solicitud de cambio) deja el mismo estado guardado por la CLI (`CliRunner`) que
por la API (cliente de pruebas), en bases separadas y con el doble falso del puerto de agente."""

from __future__ import annotations

import datetime as dt
import hashlib
import itertools
import json
import socket
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from typer.testing import CliRunner

import story_maker.cli as cli_module
import story_maker.settings as settings_module
from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import Call, FakeAgent, Say, Script
from story_maker.agents.port import AgentPort
from story_maker.api.app import create_app
from story_maker.api.auth import create_access_token
from story_maker.cli import app as cli_app
from story_maker.config import load_config
from story_maker.observability.null import NullObservability
from story_maker.policy.real_engine import RealPolicyEngine
from story_maker.store import models
from story_maker.store.brief_canon import (
    BriefCloseOne,
    BriefRecipient,
    ConfirmedBrief,
    create_generation_candidate,
)
from story_maker.store.session import (
    create_schema,
    make_engine,
    make_session_factory,
    unit_of_work,
)
from story_maker.store.versions import publish

REAL_ROOT = settings_module.ROOT
REAL_CONFIG = json.loads((REAL_ROOT / "config.json").read_text(encoding="utf-8"))
JWT_SECRET = "x" * 32
NOW = dt.datetime(2026, 9, 24, 12, 0, 0)
EMAIL = "cliente@example.com"
PASSWORD = "contraseña-larga"

runner = CliRunner()
_emails = itertools.count(1)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _write_workspace(workspace: Path) -> None:
    (workspace / "prompts").mkdir(parents=True)
    (workspace / "CLAUDE.md").write_text("Escribe en español.", encoding="utf-8")
    (workspace / "prompts" / "interviewer.md").write_text(
        "Eres el entrevistador.", encoding="utf-8"
    )
    (workspace / "prompts" / "extractor.md").write_text("Eres el extractor.", encoding="utf-8")
    (workspace / "prompts" / "planner-change.md").write_text(
        "Eres el planner en modo cambio.", encoding="utf-8"
    )


_VALID_BRIEF_PATCH: dict[str, object] = {
    "name": "Marta",
    "age": 40,
    "traits": [{"statement": "curiosa", "mandatory": False}],
    "close_ones": [
        {
            "name": "Toby",
            "relation": "mascota",
            "species": "animal",
            "age": None,
            "birth_date": None,
            "mandatory": False,
        }
    ],
    "recollections": [
        {
            "statement": "se perdió en la feria de su pueblo",
            "age": 8,
            "year": None,
            "place": "la feria de Albarracín",
            "present": [],
            "excluded": None,
            "mandatory": True,
        }
    ],
    "occasion": "birthday",
    "genre": "adventure",
    "tone": "tender",
    "length": "medium",
    "dedication": "Para Marta, que siempre encuentra el camino",
    "banned_asked": True,
}

FREE_TEXT = "Marta nació en Bilbao."
SUBMIT_FACTS = {
    "facts": [
        {
            "subject": "Marta",
            "attribute": "lugar de nacimiento",
            "value": "Bilbao",
            "quote": FREE_TEXT,
        }
    ],
    "discarded_instructions": [],
}


# --- El mismo guion de entrevista: turno, texto libre, aceptar y confirmar ----------------------


def _api_interview_world(tmp_path: Path, fake: FakeAgent) -> tuple[sessionmaker[Session], int]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    engine = make_engine(tmp_path / "api.db")
    create_schema(engine)
    session_factory = make_session_factory(engine)
    workspace = tmp_path / "api-workspace"
    _write_workspace(workspace)
    config = load_config(REAL_ROOT / "config.json")
    telemetry = NullObservability()
    policy = RealPolicyEngine(session_factory, base_url="http://127.0.0.1:8000")
    port = AgentPort(
        agent=fake,
        config=config,
        ceiling=TokenCeiling(config.token_ceiling),
        policy=policy,
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace,
    )
    api_app = create_app(
        session_factory=session_factory,
        jwt_secret=JWT_SECRET,
        clock=lambda: NOW,
        agent_port=port,
        telemetry=telemetry,
        config=config,
        workspace=workspace,
        policy=policy,
    )
    client = TestClient(api_app)
    client.post("/api/auth/register", json={"email": EMAIL, "password": PASSWORD})
    token = client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD}).json()[
        "access_token"
    ]
    headers = {"Authorization": f"Bearer {token}"}
    novel_id = client.post("/api/novels", json={}, headers=headers).json()["id"]

    fake.script(
        "interviewer", None, Script(steps=(Call("update_brief", _VALID_BRIEF_PATCH), Say("ok")))
    )
    client.post(
        f"/api/novels/{novel_id}/interview/messages", json={"text": "Hola"}, headers=headers
    )

    fake.script("extractor", None, Script(steps=(Call("submit_facts", SUBMIT_FACTS),)))
    free_text = client.post(
        f"/api/novels/{novel_id}/free-texts", json={"content": FREE_TEXT}, headers=headers
    ).json()
    fact_id = free_text["verified_facts"][0]["id"]

    client.patch(
        f"/api/novels/{novel_id}/brief/extracted-facts/{fact_id}",
        json={"accepted": True},
        headers=headers,
    )
    client.post(f"/api/novels/{novel_id}/brief/confirm", headers=headers)
    return session_factory, novel_id


def _cli_interview_world(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: FakeAgent, tmp_letter: Path
) -> tuple[sessionmaker[Session], int]:
    monkeypatch.setattr(settings_module, "ROOT", tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "config.json").write_text(json.dumps(REAL_CONFIG), encoding="utf-8")
    _write_workspace(tmp_path / "backend" / "harness_workspace")
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("FORMAL_VERIFIER", "local")
    monkeypatch.setenv("STORY_MAKER_BASE_URL", f"http://127.0.0.1:{_free_port()}")
    monkeypatch.setattr(cli_module, "_build_agent", lambda settings, workspace: fake)

    init = runner.invoke(cli_app, ["init-db"])
    assert init.exit_code == 0, init.stdout

    db_path = tmp_path / "backend" / "data" / "story-maker.db"
    engine = make_engine(db_path)
    session_factory = make_session_factory(engine)
    with unit_of_work(session_factory) as uow:
        user = models.User(email=EMAIL, password_hash="h", created_at=NOW)
        uow.add(user)

    tmp_letter.mkdir(parents=True, exist_ok=True)
    letter = tmp_letter / "carta.txt"
    letter.write_text(FREE_TEXT, encoding="utf-8")

    fake.script(
        "interviewer", None, Script(steps=(Call("update_brief", _VALID_BRIEF_PATCH), Say("ok")))
    )
    fake.script("extractor", None, Script(steps=(Call("submit_facts", SUBMIT_FACTS),)))

    result = runner.invoke(
        cli_app,
        ["interview", "--email", EMAIL],
        input=f"Hola\n/texto {letter}\n/aceptar 1\n/confirmar\ns\nn\n/salir\n",
    )
    assert result.exit_code == 0, result.stdout
    novel_id = int(result.stdout.strip().splitlines()[0])
    return session_factory, novel_id


def _brief_state(session_factory: sessionmaker[Session], novel_id: int) -> tuple[str, Any]:
    with session_factory() as session:
        brief = session.query(models.Brief).filter_by(novel_id=novel_id).one()
        return brief.status, brief.content


def _facts_state(session_factory: sessionmaker[Session], novel_id: int) -> list[tuple[Any, ...]]:
    with session_factory() as session:
        facts = (
            session.query(models.ExtractedFact)
            .join(models.FreeText, models.ExtractedFact.free_text_id == models.FreeText.id)
            .filter(models.FreeText.novel_id == novel_id)
            .order_by(models.ExtractedFact.id)
            .all()
        )
        return [(f.subject, f.attribute, f.value, f.accepted, f.mandatory) for f in facts]


def test_the_same_interview_script_leaves_the_same_brief_and_facts_via_cli_and_api(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api_sf, api_novel = _api_interview_world(tmp_path / "api", FakeAgent())
    cli_sf, cli_novel = _cli_interview_world(
        tmp_path / "cli", monkeypatch, FakeAgent(), tmp_path / "cli-input"
    )

    assert _brief_state(api_sf, api_novel) == _brief_state(cli_sf, cli_novel)
    assert _facts_state(api_sf, api_novel) == _facts_state(cli_sf, cli_novel)


# --- El mismo guion de cambio: misma propuesta y mismos afectados -------------------------------


def _build_change_novel(session_factory: sessionmaker[Session]) -> tuple[int, int, int]:
    """Novela publicada con el hecho de nombre del perro Toby, usado en el capítulo 2 —
    idéntica en las dos bases para que la misma petición produzca la misma solicitud."""
    with unit_of_work(session_factory) as uow:
        user = models.User(email=EMAIL, password_hash="h", created_at=NOW)
        uow.add(user)
        uow.session.flush()
        novel = models.Novel(
            user_id=user.id, title="La aventura de Ada", embedding_model="M1", created_at=NOW
        )
        uow.add(novel)
        uow.session.flush()
        uow.add(models.Brief(novel_id=novel.id, content={}, status="confirmed"))
        novel_id, user_id = novel.id, user.id

    brief = ConfirmedBrief(
        recipient=BriefRecipient("Ada", 30, name_element_id=1, traits=()),
        close_ones=(BriefCloseOne("Toby", "perro", "animal", element_id=2, mandatory=True),),
    )
    with unit_of_work(session_factory) as uow:
        v1_id = create_generation_candidate(uow, novel_id, brief, now=NOW).id

    with unit_of_work(session_factory) as uow:
        session = uow.session
        toby = (
            session.query(models.Character).filter_by(version_id=v1_id, canonical_name="Toby").one()
        )
        toby_name = (
            session.query(models.Fact)
            .filter_by(version_id=v1_id, character_id=toby.id, attribute="name")
            .one()
        )
        uow.add(models.FactUsage(fact_id=toby_name.id, chapter=2))
        for n in (1, 2):
            text = "Ada camina por la ciudad."
            if n == 2:
                text += " Toby ladra a su lado."
            uow.add(
                models.Chapter(
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

    with unit_of_work(session_factory) as uow:
        publish(uow, v1_id, pdf_path="v1.pdf", now=NOW)

    return novel_id, user_id, toby_name_id


CHANGE_REQUEST_TEXT = "el perro se llama Nala"


def _propose(fake: FakeAgent, fact_id: int) -> None:
    proposal = {"changes": [{"fact_id": fact_id, "new_value": "Nala"}]}
    fake.script("planner", "change", Script(steps=(Call("propose_change", proposal),)))


def _api_change_world(tmp_path: Path, fake: FakeAgent) -> models.ChangeRequest:
    tmp_path.mkdir(parents=True, exist_ok=True)
    engine = make_engine(tmp_path / "api.db")
    create_schema(engine)
    session_factory = make_session_factory(engine)
    novel_id, user_id, toby_name_fact = _build_change_novel(session_factory)

    workspace = tmp_path / "api-workspace"
    _write_workspace(workspace)
    config = load_config(REAL_ROOT / "config.json")
    telemetry = NullObservability()
    policy = RealPolicyEngine(session_factory, base_url="http://127.0.0.1:8000")
    port = AgentPort(
        agent=fake,
        config=config,
        ceiling=TokenCeiling(config.token_ceiling),
        policy=policy,
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace,
    )
    api_app = create_app(
        session_factory=session_factory,
        jwt_secret=JWT_SECRET,
        clock=lambda: NOW,
        agent_port=port,
        telemetry=telemetry,
        config=config,
        workspace=workspace,
        policy=policy,
    )
    client = TestClient(api_app)
    headers = {"Authorization": f"Bearer {create_access_token(user_id, JWT_SECRET, 24, NOW)}"}

    _propose(fake, toby_name_fact)
    client.post(
        f"/api/novels/{novel_id}/change-requests",
        json={
            "selection": {"type": "fact", "fact_id": toby_name_fact},
            "request": CHANGE_REQUEST_TEXT,
        },
        headers=headers,
    )
    with session_factory() as session:
        return session.query(models.ChangeRequest).filter_by(novel_id=novel_id).one()


def _cli_change_world(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: FakeAgent
) -> models.ChangeRequest:
    monkeypatch.setattr(settings_module, "ROOT", tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "config.json").write_text(json.dumps(REAL_CONFIG), encoding="utf-8")
    _write_workspace(tmp_path / "backend" / "harness_workspace")
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("FORMAL_VERIFIER", "local")
    monkeypatch.setenv("STORY_MAKER_BASE_URL", f"http://127.0.0.1:{_free_port()}")
    monkeypatch.setattr(cli_module, "_build_agent", lambda settings, workspace: fake)

    init = runner.invoke(cli_app, ["init-db"])
    assert init.exit_code == 0, init.stdout
    db_path = tmp_path / "backend" / "data" / "story-maker.db"
    engine = make_engine(db_path)
    session_factory = make_session_factory(engine)
    novel_id, _user_id, toby_name_fact = _build_change_novel(session_factory)

    _propose(fake, toby_name_fact)
    result = runner.invoke(
        cli_app,
        [
            "change",
            str(novel_id),
            CHANGE_REQUEST_TEXT,
            "--email",
            EMAIL,
            "--fact",
            str(toby_name_fact),
        ],
        input="n\n",
    )
    assert result.exit_code == 0, result.stdout

    with session_factory() as session:
        return session.query(models.ChangeRequest).filter_by(novel_id=novel_id).one()


def test_the_same_change_script_leaves_the_same_proposal_and_affected_via_cli_and_api(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api_row = _api_change_world(tmp_path / "api", FakeAgent())
    cli_row = _cli_change_world(tmp_path / "cli", monkeypatch, FakeAgent())

    assert (api_row.status, api_row.request, api_row.proposal, api_row.affected_chapters) == (
        cli_row.status,
        cli_row.request,
        cli_row.proposal,
        cli_row.affected_chapters,
    )

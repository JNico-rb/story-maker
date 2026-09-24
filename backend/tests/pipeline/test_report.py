"""El informe de la ejecución se calcula al pedirlo (011-C30)."""

from __future__ import annotations

import datetime as dt
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    CRITERIA,
    Seed,
    chapter_call,
    editor_script,
    review,
    seed_user,
    writer_script,
)

from story_maker.agents.fake import Fail, FakeAgent, Script
from story_maker.api.app import create_app
from story_maker.api.auth import create_access_token
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.runs import resume_run
from story_maker.store.models import RoleSession, Run
from story_maker.store.session import unit_of_work

JWT_SECRET = "x" * 32
NOW = dt.datetime(2026, 9, 24, 13, 0)


def headers(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id, JWT_SECRET, 24, NOW)}"}


def scores(**overrides: int) -> dict[str, int]:
    base = dict.fromkeys(CRITERIA, 4)
    base.update({k.replace("_", "-"): v for k, v in overrides.items()})
    return base


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> TestClient:
    return TestClient(
        create_app(session_factory=session_factory, jwt_secret=JWT_SECRET, clock=lambda: NOW)
    )


def script_run(fake: FakeAgent) -> None:
    """Capítulos 1 y 2 aceptados con no bloqueantes; el 3 cae por el proveedor y, reanudado,
    agota sus tres intentos con `fidelidad-canon` bajo el umbral."""
    fake.script("writer", "write", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(review(scores(prosa=2))))
    fake.script("writer", "write", writer_script(chapter_call()))
    fake.script("editor", None, editor_script(review(scores(tono=1))))
    fake.script("writer", "write", Script(steps=(Fail(result=True),)))


def script_resumed(fake: FakeAgent) -> None:
    for mode in ("write", "rewrite", "rewrite"):
        fake.script("writer", mode, writer_script(chapter_call()))
        fake.script("editor", None, editor_script(review(scores(fidelidad_canon=1))))


async def test_the_report_is_computed_from_what_is_stored_when_asked(
    orchestrator: Orchestrator,
    fake: FakeAgent,
    client: TestClient,
    seed: Seed,
    session_factory: sessionmaker[Session],
) -> None:
    script_run(fake)
    await orchestrator.execute(seed.run_id)
    with unit_of_work(session_factory) as uow:
        resume_run(uow, seed.run_id)
        uow.session.get_one(Run, seed.run_id).status = "running"
    script_resumed(fake)
    await orchestrator.execute(seed.run_id)

    response = client.get(f"/api/runs/{seed.run_id}/report", headers=headers(seed.user_id))

    assert response.status_code == 200, response.text
    report: dict[str, Any] = response.json()
    assert (report["status"], report["reason"], report["resumes"]) == (
        "failed",
        "retries_exhausted",
        1,
    )
    with session_factory() as session:
        costs = [
            s.cost_usd or 0.0 for s in session.query(RoleSession).filter_by(run_id=seed.run_id)
        ]
    assert report["cost_usd"] == pytest.approx(sum(costs))
    assert report["cost_usd"] > 0
    assert [(a["chapter"], a["number"], a["outcome"]) for a in report["attempts"]] == [
        (1, 1, "accept"),
        (2, 1, "accept"),
        (3, 1, "rewrite"),
        (3, 2, "rewrite"),
        (3, 3, "fail"),
    ]
    by_attempt = {
        (v["chapter"], v["attempt"], v["validator"]): v["passed"] for v in report["validators"]
    }
    assert by_attempt[(1, 1, "rubrica-capitulo")] is True
    assert by_attempt[(3, 3, "rubrica-capitulo")] is False
    assert by_attempt[(3, 3, "longitud-capitulo")] is True
    assert {(c, a) for c, a, _ in by_attempt} == {(1, 1), (2, 1), (3, 1), (3, 2), (3, 3)}
    unresolved = [(d["chapter"], d["criterion"], d["blocking"]) for d in report["unresolved"]]
    assert unresolved == [
        (1, "prosa", False),
        (2, "tono", False),
        (3, "fidelidad-canon", True),
    ]
    assert report["policy_decisions"]
    assert all(d["decision"] in ("allow", "deny", "flag") for d in report["policy_decisions"])

    again = client.get(f"/api/runs/{seed.run_id}/report", headers=headers(seed.user_id))
    assert again.json() == report


def test_the_report_of_a_foreign_run_is_404(
    client: TestClient, seed: Seed, session_factory: sessionmaker[Session]
) -> None:
    with session_factory() as session:
        stranger = seed_user(session, "otro@example.com")
        session.commit()
        stranger_id = stranger.id

    response = client.get(f"/api/runs/{seed.run_id}/report", headers=headers(stranger_id))

    assert response.status_code == 404

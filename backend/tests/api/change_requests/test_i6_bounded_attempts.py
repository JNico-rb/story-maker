"""014-I6 — Una petición tiene como mucho 1 + `max_retries.change` intentos
(`ReintentosAcotados`): con el planner siempre inválido, exactamente 1 + n."""

from __future__ import annotations

import dataclasses
from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, FakeAgent, Script
from story_maker.config import Config
from story_maker.store import models

from .conftest import ClientBuilder, F, fact_selection, headers, rename

REQUEST = "el perro se llama Nala"
SPARE = 2  # guiones de sobra: si se abriera una sesión de más, el planner seguiría entregando


def _with_change_retries(config: Config, retries: int) -> Config:
    return dataclasses.replace(config, max_retries={**config.max_retries, "change": retries})


def _attempts(sf: sessionmaker[Session], f: F) -> list[tuple[int, str]]:
    with sf() as session:
        [row] = session.query(models.ChangeRequest).filter_by(novel_id=f.novel_id).all()
        assert row.status == "rejected"
        attempts = session.query(models.Attempt).filter_by(change_request_id=row.id)
        return sorted((a.number, a.outcome) for a in attempts)


def _expected(retries: int) -> list[tuple[int, str]]:
    return [(n, "rewrite") for n in range(1, retries + 1)] + [(retries + 1, "fail")]


@pytest.mark.parametrize("retries", [0, 1, 3])
def test_an_always_invalid_planner_gets_exactly_one_plus_max_retries_sessions(
    build_client: ClientBuilder,
    config: Config,
    f: F,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    retries: int,
) -> None:
    client, _ = build_client(_with_change_retries(config, retries))
    for _ in range(1 + retries + SPARE):
        fake.script(
            "planner",
            "change",
            Script(steps=(Call("propose_change", rename(f.toby_name_fact, "Toby")),)),
        )

    response = _post(client, f)

    assert response.status_code == 422, response.text
    assert len(fake.sessions) == 1 + retries
    assert _attempts(session_factory, f) == _expected(retries)


@pytest.mark.parametrize("retries", [0, 1, 3])
def test_schema_errors_in_one_session_are_cut_at_one_plus_max_retries(
    build_client: ClientBuilder,
    config: Config,
    f: F,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    retries: int,
) -> None:
    client, _ = build_client(_with_change_retries(config, retries))
    steps = tuple(Call("propose_change", {}) for _ in range(1 + retries + SPARE))
    fake.script("planner", "change", Script(steps=steps))
    fake.script("planner", "change", Script(steps=steps))

    response = _post(client, f)

    assert response.status_code == 422, response.text
    assert len(fake.sessions) == 1
    assert _attempts(session_factory, f) == _expected(retries)


def _post(client: Any, f: F) -> Any:
    return client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": REQUEST},
        headers=headers(f.user_a),
    )

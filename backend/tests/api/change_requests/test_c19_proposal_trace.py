"""014-C19 — Cada propuesta deja su traza: un span `rol:planner` por sesión con su llamada de
modelo, y la solicitud guarda la clave de esa traza para sumar al coste de la revisión las
sesiones de rol de la propuesta. La traza de la ejecución está en
`tests/pipeline/changes/test_change_traces.py`."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, FakeAgent, Script
from story_maker.agents.usage import Usage, cost_usd
from story_maker.config import Config
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Span
from story_maker.pipeline.changes.cost import revision_cost
from story_maker.store import models
from story_maker.store.session import unit_of_work

from .conftest import F, fact_selection, headers, rename

REQUEST = "el perro se llama Nala"
FIRST = Usage(input_tokens=1200, output_tokens=300, cache_read_tokens=100, cache_write_tokens=50)
SECOND = Usage(input_tokens=1500, output_tokens=200, cache_read_tokens=0, cache_write_tokens=0)
MISSING_FACT = 999_999


def _planner(fake: FakeAgent, proposal: dict[str, object], usage: Usage) -> None:
    fake.script("planner", "change", Script(steps=(Call("propose_change", proposal),), usage=usage))


def _role_spans(spans: list[Span]) -> list[Span]:
    return [s for span in spans for s in (span, *_role_spans(span.children))]


def test_each_planner_session_of_a_proposal_leaves_a_role_span_with_its_model_call(
    client: TestClient, f: F, fake: FakeAgent, telemetry: NullObservability, config: Config
) -> None:
    _planner(fake, rename(MISSING_FACT, "Nala"), FIRST)
    _planner(fake, rename(f.toby_name_fact, "Nala"), SECOND)

    response = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": REQUEST},
        headers=headers(f.user_a),
    )

    assert response.status_code == 201, response.text
    (trace,) = telemetry.traces.values()
    assert (trace.name, trace.session) == ("propuesta-de-cambio", str(f.novel_id))
    roles = [s for s in _role_spans(trace.spans) if s.name == "rol:planner"]
    assert len(roles) == 2
    model = config.roles["planner"].model
    for span, usage in zip(roles, (FIRST, SECOND), strict=True):
        (call,) = span.model_calls
        assert call.model == model
        assert call.prompt_version is None  # el doble nulo no da versión (§13.6)
        assert (call.input_tokens, call.output_tokens) == (usage.input_tokens, usage.output_tokens)
        assert (call.cache_read_tokens, call.cache_write_tokens) == (
            usage.cache_read_tokens,
            usage.cache_write_tokens,
        )
        assert call.cost_usd == cost_usd(usage, config.pricing[model])
        assert call.latency_ms >= 0
        tools = [c.name for c in span.children]
        assert "tool:propose_change" in tools


def _ask(client: TestClient, f: F, request: str = REQUEST) -> dict[str, object]:
    response = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": request},
        headers=headers(f.user_a),
    )
    return response.json()  # type: ignore[no-any-return]


def test_the_request_keeps_the_key_of_its_proposal_trace_shared_by_its_planner_sessions(
    client: TestClient,
    f: F,
    fake: FakeAgent,
    telemetry: NullObservability,
    session_factory: sessionmaker[Session],
) -> None:
    _planner(fake, rename(MISSING_FACT, "Nala"), FIRST)
    _planner(fake, rename(f.toby_name_fact, "Nala"), SECOND)

    body = _ask(client, f)

    (key,) = telemetry.traces
    with session_factory() as session:
        row = session.get_one(models.ChangeRequest, body["id"])
        assert row.proposal_trace == key
        sessions = session.query(models.RoleSession).filter_by(trace_id=key).all()
        assert [s.role for s in sessions] == ["planner", "planner"]


def test_a_denied_request_also_keeps_the_key_of_its_proposal_trace(
    client: TestClient,
    f: F,
    telemetry: NullObservability,
    session_factory: sessionmaker[Session],
) -> None:
    _ask(client, f, "que el perro se llame Zoquete")

    (key,) = telemetry.traces
    with session_factory() as session:
        (row,) = session.query(models.ChangeRequest).all()
        assert (row.status, row.proposal_trace) == ("rejected", key)


def _role_session(
    sf: sessionmaker[Session], novel_id: int, cost: float, *, run_id: int | None, trace: str
) -> None:
    with unit_of_work(sf) as uow:
        uow.add(
            models.RoleSession(
                novel_id=novel_id,
                run_id=run_id,
                role="writer" if run_id else "planner",
                model="m",
                reserved_tokens=1,
                cost_usd=cost,
                latency_ms=1,
                outcome="completed",
                trace_id=trace,
            )
        )


def test_the_revision_cost_adds_the_proposal_sessions_and_the_run_sessions(
    client: TestClient,
    f: F,
    fake: FakeAgent,
    config: Config,
    session_factory: sessionmaker[Session],
) -> None:
    _planner(fake, rename(MISSING_FACT, "Nala"), FIRST)
    _planner(fake, rename(f.toby_name_fact, "Nala"), SECOND)
    body = _ask(client, f)
    run_id = client.post(
        f"/api/change-requests/{body['id']}/confirm",
        json={"code": body["code"]},
        headers=headers(f.user_a),
    ).json()["run_id"]
    _role_session(session_factory, f.novel_id, 0.25, run_id=run_id, trace=f"run:{run_id}")
    _role_session(session_factory, f.novel_id, 0.5, run_id=run_id, trace=f"run:{run_id}")
    _role_session(session_factory, f.novel_id, 9.0, run_id=None, trace="propuesta-de-cambio:x")
    price = config.pricing[config.roles["planner"].model]

    with session_factory() as session:
        cost = revision_cost(session, session.get_one(models.ChangeRequest, body["id"]))

    expected = cost_usd(FIRST, price) + cost_usd(SECOND, price) + 0.75
    assert abs(cost - expected) < 1e-12

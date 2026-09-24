"""Trazas y scores de la entrevista y de la importación (008-C31)."""

from __future__ import annotations

import copy

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, FakeAgent, Say, Script
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Span
from story_maker.store.models import BannedTerm

from .briefs import B0_CONTENT, seed_brief
from .test_free_text_extraction import FACTS, LETTER
from .test_novel_import_valid import _import_body


def _flatten(spans: list[Span]) -> list[Span]:
    out: list[Span] = []
    for span in spans:
        out.append(span)
        out.extend(_flatten(span.children))
    return out


def _novel_missing_dedication_with_pedro_banned(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> int:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    content = copy.deepcopy(B0_CONTENT)
    content["dedication"] = ""
    seed_brief(session_factory, novel_id, content)
    with session_factory() as session:
        session.add(
            BannedTerm(
                level="novel",
                user_id=None,
                novel_id=novel_id,
                term="pedro",
                type="word",
                keywords=None,
                normalized="pedro",
            )
        )
        session.commit()
    return novel_id


def _run_interview_scenario(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> int:
    novel_id = _novel_missing_dedication_with_pedro_banned(client, auth_headers, session_factory)

    # Turno 1: un update_brief permitido.
    fake.script(
        "interviewer",
        None,
        Script(steps=(Call("update_brief", {"tone": "funny"}), Say("¿Y la dedicatoria?"))),
    )
    turn1 = client.post(
        f"/api/novels/{novel_id}/interview/messages",
        json={"text": "Que sea divertida"},
        headers=auth_headers,
    )
    assert turn1.status_code == 200

    # Confirmación rechazada: falta la dedicatoria.
    rejected = client.post(f"/api/novels/{novel_id}/brief/confirm", headers=auth_headers)
    assert rejected.status_code == 422

    # Turno 2: una entrega denegada (dedicatoria con "Pedro") y otra permitida.
    fake.script(
        "interviewer",
        None,
        Script(
            steps=(
                Call("update_brief", {"dedication": "Para Marta, lejos de Pedro"}),
                Call("update_brief", {"dedication": "Para Marta, que siempre encuentra el camino"}),
                Say("Ya está."),
            )
        ),
    )
    turn2 = client.post(
        f"/api/novels/{novel_id}/interview/messages",
        json={"text": "Pon una dedicatoria"},
        headers=auth_headers,
    )
    assert turn2.status_code == 200

    # Un texto libre.
    fake.script(
        "extractor",
        None,
        Script(steps=(Call("submit_facts", {"facts": FACTS, "discarded_instructions": []}),)),
    )
    free_text = client.post(
        f"/api/novels/{novel_id}/free-texts", json={"content": LETTER}, headers=auth_headers
    )
    assert free_text.status_code == 201

    # Confirmación aceptada.
    accepted = client.post(f"/api/novels/{novel_id}/brief/confirm", headers=auth_headers)
    assert accepted.status_code == 200

    return novel_id


def test_the_whole_interview_shares_one_trace_with_its_spans_and_scores(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
    telemetry: object,
) -> None:
    assert isinstance(telemetry, NullObservability)
    novel_id = _run_interview_scenario(client, auth_headers, session_factory, fake)

    trace = telemetry.traces[f"interview:{novel_id}"]
    assert trace.name == "entrevista"
    assert trace.session == str(novel_id)

    all_spans = _flatten(trace.spans)
    span_names = [s.name for s in all_spans]
    assert span_names.count("rol:entrevistador") == 2
    assert span_names.count("rol:extractor") == 1
    update_brief_spans = [s for s in all_spans if s.name == "tool:update_brief"]
    assert len(update_brief_spans) == 3
    assert any(s.level == "WARNING" for s in update_brief_spans)

    citas = [s for s in trace.scores if s.name == "citas-verificadas"]
    assert len(citas) == 1

    schema_brief = [s for s in trace.scores if s.name == "schema-brief"]
    assert [s.value for s in schema_brief] == [0, 1]


def test_reads_banned_lists_and_the_fact_patch_send_nothing_to_the_trace(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
    telemetry: object,
) -> None:
    assert isinstance(telemetry, NullObservability)
    novel_id = _run_interview_scenario(client, auth_headers, session_factory, fake)
    trace = telemetry.traces[f"interview:{novel_id}"]
    spans_before = len(_flatten(trace.spans))
    scores_before = len(trace.scores)

    client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers)
    client.get(f"/api/novels/{novel_id}", headers=auth_headers)
    client.get(f"/api/novels/{novel_id}/banned-terms", headers=auth_headers)

    fact_id = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()[
        "verified_facts"
    ][0]["id"]
    # El brief ya está confirmado: el PATCH se rechaza, pero tampoco debe enviar nada a la traza.
    client.patch(
        f"/api/novels/{novel_id}/brief/extracted-facts/{fact_id}",
        json={"accepted": True},
        headers=auth_headers,
    )

    assert len(_flatten(trace.spans)) == spans_before
    assert len(trace.scores) == scores_before


def test_turns_never_send_a_schema_brief_score(
    client: TestClient,
    auth_headers: dict[str, str],
    fake: FakeAgent,
    telemetry: object,
) -> None:
    assert isinstance(telemetry, NullObservability)
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    fake.script(
        "interviewer", None, Script(steps=(Call("update_brief", {"tone": "funny"}), Say("ok")))
    )
    client.post(
        f"/api/novels/{novel_id}/interview/messages",
        json={"text": "hola"},
        headers=auth_headers,
    )

    trace = telemetry.traces[f"interview:{novel_id}"]
    assert "schema-brief" not in [s.name for s in trace.scores]


def test_the_import_goes_to_its_own_trace(
    client: TestClient, auth_headers: dict[str, str], fake: FakeAgent, telemetry: object
) -> None:
    assert isinstance(telemetry, NullObservability)
    fake.script(
        "extractor",
        None,
        Script(steps=(Call("submit_facts", {"facts": FACTS, "discarded_instructions": []}),)),
    )
    response = client.post("/api/novels", json=_import_body(), headers=auth_headers)
    novel_id = response.json()["id"]

    assert f"interview:{novel_id}" not in telemetry.traces
    trace = telemetry.traces[f"import:{novel_id}"]
    assert trace.name == "importacion"

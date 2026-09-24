"""Importar un brief válido (008-C28)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, FakeAgent, Script
from story_maker.store.models import BannedTerm, Brief, ExtractedFact, FreeText, InterviewMessage

from .briefs import B0_CONTENT
from .test_free_text_extraction import FACTS, LETTER


def _import_body() -> dict[str, object]:
    return {
        **B0_CONTENT,
        "banned_entries": [{"term": "Pedro", "type": "word", "keywords": []}],
        "free_texts": [LETTER],
    }


def _post_import(
    client: TestClient, auth_headers: dict[str, str], fake: FakeAgent
) -> dict[str, object]:
    fake.script(
        "extractor",
        None,
        Script(steps=(Call("submit_facts", {"facts": FACTS, "discarded_instructions": []}),)),
    )
    response = client.post("/api/novels", json=_import_body(), headers=auth_headers)
    assert response.status_code == 201, response.json()
    return response.json()  # type: ignore[no-any-return]


def test_importing_b0_confirms_the_brief_and_the_novel_is_ready(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    body = _post_import(client, auth_headers, fake)
    novel_id = body["id"]

    detail = client.get(f"/api/novels/{novel_id}", headers=auth_headers).json()
    assert detail["status"] == "ready"

    with session_factory() as session:
        brief = session.query(Brief).filter(Brief.novel_id == novel_id).one()
        assert brief.status == "confirmed"
        assert session.query(InterviewMessage).count() == 0


def test_importing_runs_the_extractor_once_and_accepts_tobys_fact_unmarked(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    body = _post_import(client, auth_headers, fake)
    novel_id = body["id"]

    assert len(fake.sessions) == 1
    assert fake.sessions[0].request.role == "extractor"

    with session_factory() as session:
        free_texts = session.query(FreeText).filter(FreeText.novel_id == novel_id).all()
        assert len(free_texts) == 1
        facts = (
            session.query(ExtractedFact)
            .filter(ExtractedFact.free_text_id == free_texts[0].id)
            .order_by(ExtractedFact.id)
            .all()
        )
        toby = next(f for f in facts if f.subject == "Toby")
        assert toby.accepted is True
        assert toby.mandatory is False


def test_pedro_ends_up_as_a_novel_level_banned_entry(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    body = _post_import(client, auth_headers, fake)
    novel_id = body["id"]

    with session_factory() as session:
        entry = session.query(BannedTerm).filter(BannedTerm.novel_id == novel_id).one()
        assert entry.term == "Pedro"
        assert entry.level == "novel"


def test_the_import_trace_has_schema_brief_1_and_citas_verificadas_0_with_2_discarded(
    client: TestClient,
    auth_headers: dict[str, str],
    fake: FakeAgent,
    telemetry: object,
) -> None:
    from story_maker.observability.null import NullObservability

    assert isinstance(telemetry, NullObservability)
    body = _post_import(client, auth_headers, fake)
    novel_id = body["id"]

    trace = telemetry.traces[f"import:{novel_id}"]
    schema_brief = [s for s in trace.scores if s.name == "schema-brief"]
    assert [s.value for s in schema_brief] == [1]
    citas = [s for s in trace.scores if s.name == "citas-verificadas"]
    assert [s.value for s in citas] == [0]
    assert citas[0].comment is not None
    assert "2" in citas[0].comment

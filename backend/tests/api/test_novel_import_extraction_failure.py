"""Importación con una extracción fallida (008-C30)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, Fail, FakeAgent, Script
from story_maker.store.models import Brief, ExtractedFact, FreeText, RoleSession

from .briefs import B0_CONTENT
from .test_free_text_extraction import FACTS, LETTER

SECOND_LETTER = "Querida Marta: da igual, el proveedor fallará antes de decir nada."


def _import_body() -> dict[str, object]:
    return {**B0_CONTENT, "free_texts": [LETTER, SECOND_LETTER]}


def test_the_second_extraction_failing_answers_503_with_novel_id_and_reason(
    client: TestClient, auth_headers: dict[str, str], fake: FakeAgent
) -> None:
    fake.script(
        "extractor",
        None,
        Script(steps=(Call("submit_facts", {"facts": FACTS, "discarded_instructions": []}),)),
    )
    fake.script("extractor", None, Script(steps=(Fail(result=True),)))

    response = client.post("/api/novels", json=_import_body(), headers=auth_headers)

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert "novel_id" in detail
    assert detail["reason"]


def test_the_novel_stays_in_interview_with_the_first_texts_facts_accepted_and_not_mandatory(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    fake.script(
        "extractor",
        None,
        Script(steps=(Call("submit_facts", {"facts": FACTS, "discarded_instructions": []}),)),
    )
    fake.script("extractor", None, Script(steps=(Fail(result=True),)))

    response = client.post("/api/novels", json=_import_body(), headers=auth_headers)
    novel_id = response.json()["detail"]["novel_id"]

    detail = client.get(f"/api/novels/{novel_id}", headers=auth_headers).json()
    assert detail["status"] == "interview"

    with session_factory() as session:
        brief = session.query(Brief).filter(Brief.novel_id == novel_id).one()
        assert brief.status == "draft"
        assert brief.content["recipient"]["name"] == "Marta"

        free_texts = session.query(FreeText).filter(FreeText.novel_id == novel_id).all()
        assert len(free_texts) == 1
        assert free_texts[0].content == LETTER

        facts = (
            session.query(ExtractedFact)
            .filter(ExtractedFact.free_text_id == free_texts[0].id)
            .order_by(ExtractedFact.id)
            .all()
        )
        toby = next(f for f in facts if f.subject == "Toby")
        assert toby.accepted is True
        assert toby.mandatory is False


def test_both_role_sessions_are_saved_even_though_the_second_failed(
    client: TestClient,
    auth_headers: dict[str, str],
    session_factory: sessionmaker[Session],
    fake: FakeAgent,
) -> None:
    fake.script(
        "extractor",
        None,
        Script(steps=(Call("submit_facts", {"facts": FACTS, "discarded_instructions": []}),)),
    )
    fake.script("extractor", None, Script(steps=(Fail(result=True),)))

    client.post("/api/novels", json=_import_body(), headers=auth_headers)

    with session_factory() as session:
        assert session.query(RoleSession).filter(RoleSession.role == "extractor").count() == 2


def test_the_client_resumes_by_sending_the_second_text_through_the_interview(
    client: TestClient, auth_headers: dict[str, str], fake: FakeAgent
) -> None:
    fake.script(
        "extractor",
        None,
        Script(steps=(Call("submit_facts", {"facts": FACTS, "discarded_instructions": []}),)),
    )
    fake.script("extractor", None, Script(steps=(Fail(result=True),)))
    response = client.post("/api/novels", json=_import_body(), headers=auth_headers)
    novel_id = response.json()["detail"]["novel_id"]

    fake.script(
        "extractor",
        None,
        Script(
            steps=(
                Call(
                    "submit_facts",
                    {
                        "facts": [
                            {
                                "subject": "Marta",
                                "attribute": "opinión",
                                "value": "el proveedor fallará",
                                "quote": "el proveedor fallará",
                            }
                        ],
                        "discarded_instructions": [],
                    },
                ),
            )
        ),
    )
    retry = client.post(
        f"/api/novels/{novel_id}/free-texts",
        json={"content": SECOND_LETTER},
        headers=auth_headers,
    )

    assert retry.status_code == 201
    assert len(retry.json()["verified_facts"]) == 1

    confirm = client.post(f"/api/novels/{novel_id}/brief/confirm", headers=auth_headers)
    assert confirm.status_code == 200
    assert confirm.json()["status"] == "confirmed"

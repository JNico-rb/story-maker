"""Aceptar, rechazar y marcar obligatorio un hecho extraído (008-C24)."""

from __future__ import annotations

import datetime as dt

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.store.models import ExtractedFact, FreeText

from .briefs import B0_CONTENT, seed_brief

NOW = dt.datetime(2026, 9, 24, 12, 0)


def _seed_fact(
    session_factory: sessionmaker[Session],
    novel_id: int,
    *,
    verified: bool = True,
    accepted: bool | None = None,
    mandatory: bool = False,
) -> int:
    with session_factory() as session:
        free_text = session.query(FreeText).filter(FreeText.novel_id == novel_id).one_or_none()
        if free_text is None:
            free_text = FreeText(
                novel_id=novel_id, content="x", discarded_instructions=None, created_at=NOW
            )
            session.add(free_text)
            session.flush()
        fact = ExtractedFact(
            free_text_id=free_text.id,
            subject="Marta",
            attribute="algo",
            value="un valor",
            quote="un valor",
            verified=verified,
            accepted=accepted,
            mandatory=mandatory,
        )
        session.add(fact)
        session.commit()
        return fact.id


def _new_novel(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> int:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)
    return novel_id


def test_accepting_a_verified_fact_makes_it_part_of_the_brief(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = _new_novel(client, auth_headers, session_factory)
    fact_id = _seed_fact(session_factory, novel_id)

    response = client.patch(
        f"/api/novels/{novel_id}/brief/extracted-facts/{fact_id}",
        json={"accepted": True},
        headers=auth_headers,
    )

    assert response.status_code == 200
    facts = [e for e in response.json()["personal_elements"] if e["origin"] == "extracted_fact"]
    assert len(facts) == 1


def test_accepting_and_marking_mandatory_counts_toward_the_cap(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = _new_novel(client, auth_headers, session_factory)
    fact_id = _seed_fact(session_factory, novel_id)
    before = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()

    response = client.patch(
        f"/api/novels/{novel_id}/brief/extracted-facts/{fact_id}",
        json={"accepted": True, "mandatory": True},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["mandatory_count"] == before["mandatory_count"] + 1


def test_rejecting_an_accepted_fact_removes_it_and_its_mandatory_flag(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = _new_novel(client, auth_headers, session_factory)
    fact_id = _seed_fact(session_factory, novel_id, accepted=True, mandatory=True)

    response = client.patch(
        f"/api/novels/{novel_id}/brief/extracted-facts/{fact_id}",
        json={"accepted": False},
        headers=auth_headers,
    )

    assert response.status_code == 200
    facts = [e for e in response.json()["personal_elements"] if e["origin"] == "extracted_fact"]
    assert facts == []
    with session_factory() as session:
        fact = session.get(ExtractedFact, fact_id)
        assert fact is not None
        assert fact.mandatory is False


def test_marking_mandatory_an_unaccepted_fact_is_rejected(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = _new_novel(client, auth_headers, session_factory)
    fact_id = _seed_fact(session_factory, novel_id)

    response = client.patch(
        f"/api/novels/{novel_id}/brief/extracted-facts/{fact_id}",
        json={"mandatory": True},
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_an_unverified_facts_id_from_the_same_novel_answers_404(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = _new_novel(client, auth_headers, session_factory)
    fact_id = _seed_fact(session_factory, novel_id, verified=False)

    response = client.patch(
        f"/api/novels/{novel_id}/brief/extracted-facts/{fact_id}",
        json={"accepted": True},
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_a_facts_id_from_another_novel_of_the_same_client_answers_404(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = _new_novel(client, auth_headers, session_factory)
    other_novel_id = _new_novel(client, auth_headers, session_factory)
    fact_id = _seed_fact(session_factory, other_novel_id)

    response = client.patch(
        f"/api/novels/{novel_id}/brief/extracted-facts/{fact_id}",
        json={"accepted": True},
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_a_confirmed_brief_answers_409(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = _new_novel(client, auth_headers, session_factory)
    fact_id = _seed_fact(session_factory, novel_id)
    seed_brief(session_factory, novel_id, B0_CONTENT, status="confirmed")

    response = client.patch(
        f"/api/novels/{novel_id}/brief/extracted-facts/{fact_id}",
        json={"accepted": True},
        headers=auth_headers,
    )

    assert response.status_code == 409

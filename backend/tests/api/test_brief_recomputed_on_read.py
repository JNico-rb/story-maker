"""Las comprobaciones se recalculan en cada lectura, sin que medie ningún turno (008-C14)."""

from __future__ import annotations

import datetime as dt

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.store.models import ExtractedFact, FreeText

from .briefs import B0_CONTENT, seed_brief

NOW = dt.datetime(2026, 9, 24, 12, 0)


def test_a_new_user_banned_term_and_its_removal_change_c6_on_the_next_read(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)

    added = client.post(
        "/api/banned-terms",
        json={"term": "camino", "type": "word"},
        headers=auth_headers,
    )
    assert added.status_code == 201
    term_id = added.json()["id"]

    first_read = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()
    assert any(c["rule"] == "C6" for c in first_read["contradictions"])

    removed = client.delete(f"/api/banned-terms/{term_id}", headers=auth_headers)
    assert removed.status_code == 204

    second_read = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()
    assert not any(c["rule"] == "C6" for c in second_read["contradictions"])


def test_marking_an_accepted_fact_mandatory_raises_the_cap_on_the_next_read(
    client: TestClient, auth_headers: dict[str, str], session_factory: sessionmaker[Session]
) -> None:
    novel_id = client.post("/api/novels", json={}, headers=auth_headers).json()["id"]
    seed_brief(session_factory, novel_id, B0_CONTENT)
    with session_factory() as session:
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
            verified=True,
            accepted=True,
            mandatory=False,
        )
        session.add(fact)
        session.commit()
        fact_id = fact.id

    before = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()
    before_count = before["mandatory_count"]

    patched = client.patch(
        f"/api/novels/{novel_id}/brief/extracted-facts/{fact_id}",
        json={"mandatory": True},
        headers=auth_headers,
    )
    assert patched.status_code == 200

    after = client.get(f"/api/novels/{novel_id}/brief", headers=auth_headers).json()
    assert after["mandatory_count"] == before_count + 1

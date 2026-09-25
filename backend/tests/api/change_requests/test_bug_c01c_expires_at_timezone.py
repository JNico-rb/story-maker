"""014-bug-C01c — `expires_at` sale en UTC con huso (`architecture.md` §15.7, «Forma común»):
sin huso, un navegador al oeste de UTC lo lee como hora local y la propuesta sale caducada al
instante."""

from __future__ import annotations

import datetime as dt

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import FakeAgent
from story_maker.store import models

from .conftest import F, MutableClock, fact_selection, headers, propose, rename


def test_expires_at_carries_the_utc_offset(
    client: TestClient,
    f: F,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    clock: MutableClock,
) -> None:
    propose(fake, rename(f.toby_name_fact, "Nala"))

    response = client.post(
        f"/api/novels/{f.novel_id}/change-requests",
        json={"selection": fact_selection(f.toby_name_fact), "request": "el perro se llama Nala"},
        headers=headers(f.user_a),
    )

    assert response.status_code == 201, response.text
    expires_at = response.json()["expires_at"]
    parsed = dt.datetime.fromisoformat(str(expires_at))
    assert parsed.tzinfo is not None
    with session_factory() as session:
        row = session.get_one(models.ChangeRequest, response.json()["id"])
        assert parsed == row.expires_at.replace(tzinfo=dt.UTC)
    assert parsed == clock.now.replace(tzinfo=dt.UTC) + dt.timedelta(minutes=15)

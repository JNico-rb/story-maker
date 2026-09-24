"""Brief de referencia B0 (spec `008-brief-y-entrevista.md`, «Brief de referencia B0») y su
siembra directa en el store, para las pruebas que parten de un borrador ya relleno."""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from story_maker.store.models import Brief

NOVEL_CREATED_AT = dt.datetime(2026, 9, 24, 12, 0)
MAX_MANDATORY_ELEMENTS = 8

B0_CONTENT: dict[str, Any] = {
    "recipient": {
        "name": "Marta",
        "age": 40,
        "birth_date": None,
        "traits": [{"statement": "curiosa", "mandatory": False}],
        "relation": None,
    },
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
    "plot_wishes": [{"statement": "que salga un robot"}],
}


def seed_brief(
    session_factory: sessionmaker[Session],
    novel_id: int,
    content: dict[str, Any],
    *,
    status: str = "draft",
) -> None:
    with session_factory() as session:
        brief = session.query(Brief).filter(Brief.novel_id == novel_id).one()
        brief.content = content
        brief.status = status
        session.commit()

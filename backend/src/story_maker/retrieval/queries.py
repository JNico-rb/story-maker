"""Las dos consultas: la prospectiva del writer y la retrospectiva del editor
(`architecture.md` §6.2)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from story_maker.retrieval.embedding import EmbeddingModel
from story_maker.retrieval.retriever import retrieve
from story_maker.store.models import CanonCard, Event, OutlineChapter


def prospective_query(session: Session, version_id: int, chapter: int) -> list[str]:
    """Un fragmento por beat del capítulo `chapter` del outline de la versión: su descripción y
    los enunciados de sus eventos planificados. Nunca texto de capítulos ni otros beats."""
    outline = session.scalars(
        select(OutlineChapter).where(
            OutlineChapter.version_id == version_id, OutlineChapter.number == chapter
        )
    ).one()
    beats = sorted(cast(list[dict[str, Any]], outline.beats), key=lambda beat: beat["number"])
    events = session.scalars(
        select(Event)
        .where(
            Event.version_id == version_id,
            Event.origin == "planned",
            Event.chapter == chapter,
        )
        .order_by(Event.moment, Event.statement)
    ).all()
    return [
        "\n".join([beat["description"], *(e.statement for e in events if e.beat == beat["number"])])
        for beat in beats
    ]


def retrieve_for_writer(
    session: Session,
    version_id: int,
    chapter: int,
    top_k: Mapping[str, int],
    embedder: EmbeddingModel,
) -> list[CanonCard]:
    """Las `top_k["writer"]` tarjetas del writer del capítulo, en cualquiera de sus modos."""
    query = prospective_query(session, version_id, chapter)
    return retrieve(session, version_id, chapter, query, top_k["writer"], embedder)

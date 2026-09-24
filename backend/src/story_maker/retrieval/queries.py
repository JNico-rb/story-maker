"""Las dos consultas: la prospectiva del writer y la retrospectiva del editor
(`architecture.md` §6.2)."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from story_maker.retrieval.embedding import EmbeddingModel
from story_maker.retrieval.retriever import retrieve
from story_maker.store.models import CanonCard, Event, OutlineChapter

_BLANK_LINE = re.compile(r"\n\s*\n")


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


def retrospective_query(text: str) -> list[str]:
    """Un fragmento por párrafo del texto que recibe el editor (párrafos separados por una
    línea en blanco, `definitions.md` §3)."""
    paragraphs = (paragraph.strip() for paragraph in _BLANK_LINE.split(text))
    return [paragraph for paragraph in paragraphs if paragraph]


def retrieve_for_editor(
    session: Session,
    version_id: int,
    chapter: int,
    text: str,
    top_k: Mapping[str, int],
    embedder: EmbeddingModel,
) -> list[CanonCard]:
    """Las `top_k["editor"]` tarjetas del editor del capítulo, con el texto que revisa."""
    query = retrospective_query(text)
    return retrieve(session, version_id, chapter, query, top_k["editor"], embedder)

"""Máscara de una novela para las trazas MCP: nombres y fechas del brief, nunca del texto
generado (`architecture.md` §13.5; 015-C17, 015-I10). `list_novels` toca varias novelas: su
máscara es la unión de las de cada una (`Mask.__or__`, ya prevista en 004-C11)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from story_maker.domain.brief import BriefContent
from story_maker.interview.novels import brief_of
from story_maker.observability.mask import Mask


def mask_for_novel(session: Session, novel_id: int) -> Mask:
    brief = brief_of(session, novel_id)
    content = BriefContent.model_validate(brief.content) if brief.content else BriefContent()
    names = [content.recipient.name, *(c.name for c in content.close_ones)]
    dates = [
        str(d)
        for d in (content.recipient.birth_date, *(c.birth_date for c in content.close_ones))
        if d is not None
    ]
    return Mask(names=tuple(n for n in names if n), dates=tuple(dates))

"""La etapa 3 del `GateDePublicacion`: `revision-visual` sobre la `VistaDeVersion` de la
candidata (`architecture.md` §9.4, §11.2; spec 017)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from story_maker.render.view_data import load_version_view_data
from story_maker.store.models import Version
from story_maker.validators.visual_review import (
    ExpectedChapter,
    ExpectedCover,
    ExpectedEntity,
    ExpectedStructure,
)


def expected_structure(session: Session, version_id: int) -> ExpectedStructure:
    """Lo que debe mostrar la vista de la candidata, con los mismos datos que la pinta (013):
    solo la candidata, nunca su base (017-C01)."""
    data = load_version_view_data(session, session.get_one(Version, version_id))
    chapters = tuple(ExpectedChapter(c.number, c.title, c.text) for c in data.chapters)
    return ExpectedStructure(
        cover=ExpectedCover(data.title, data.recipient, data.dedication),
        index=tuple(c.number for c in chapters),
        chapters=chapters,
        ficha=tuple(ExpectedEntity(e.name, e.kind, frozenset(e.chapters)) for e in data.ficha),
    )

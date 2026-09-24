"""La selección de una solicitud de cambio: un hecho o un fragmento (versión, capítulo y cita)
(`definitions.md` §5 SolicitudDeCambio), y sus comprobaciones antes de la policy (014-C03)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from story_maker.store.models import Chapter, Fact, Version

FIRST_CHAPTER = 1
LAST_CHAPTER = 10


class FactSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["fact"]
    fact_id: int


class FragmentSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["fragment"]
    version: int
    chapter: int
    quote: str


Selection = Annotated[FactSelection | FragmentSelection, Field(discriminator="type")]


def selection_obstacle(
    session: Session, novel_id: int, base: Version, selection: FactSelection | FragmentSelection
) -> tuple[int, str] | None:
    """El código HTTP y el motivo por el que la selección no admite una petición, o ninguno:
    409 si es de una versión de la novela que ya no es la vigente, 422 si no es de ninguna."""
    if isinstance(selection, FactSelection):
        fact = session.get(Fact, selection.fact_id)
        version = session.get(Version, fact.version_id) if fact is not None else None
        if version is None or version.novel_id != novel_id:
            return 422, "el hecho no existe en ninguna versión de la novela"
        if version.id != base.id:
            return 409, "el hecho es de una versión que ya no es la vigente"
        return None
    if not FIRST_CHAPTER <= selection.chapter <= LAST_CHAPTER:
        return 422, "el capítulo del fragmento está fuera de 1-10"
    if selection.version != base.number:
        return 409, "el fragmento es de una versión que ya no es la vigente"
    chapter = (
        session.query(Chapter)
        .filter(Chapter.version_id == base.id, Chapter.number == selection.chapter)
        .one_or_none()
    )
    if (
        chapter is None
        or not _collapse(selection.quote)
        or (_collapse(selection.quote) not in _collapse(chapter.text))
    ):
        return 422, "la cita no aparece literal en su capítulo"
    return None


def _collapse(text: str) -> str:
    return " ".join(text.split())

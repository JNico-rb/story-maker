"""Vista del brief confirmado que necesita la ventana del planner (010-C06).

Como `story_bible_view.py`: una vista mínima, pensada para que quien arranque la fase la
construya desde el brief de 008 (`interview/`) una vez esa spec esté en V2; hasta entonces la
construyen las pruebas directamente. Solo lleva lo que el planner puede ver: nunca el texto
libre ni la cita de un `HechoExtraido` (010-I1)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TraitView:
    statement: str
    mandatory: bool


@dataclass(frozen=True)
class CloseOneView:
    name: str
    relationship: str
    species: str
    mandatory: bool


@dataclass(frozen=True)
class RecollectionView:
    statement: str
    place: str
    present: tuple[str, ...]
    excluded: str | None
    mandatory: bool


@dataclass(frozen=True)
class ExtractedFactView:
    """Solo lo que entra en la ventana: sujeto, atributo y valor, nunca la cita (010-C06)."""

    subject: str
    attribute: str
    value: str


@dataclass(frozen=True)
class BannedEntryView:
    term: str
    type: str
    keywords: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecipientView:
    name: str
    age: int
    traits: tuple[TraitView, ...] = ()


@dataclass(frozen=True)
class BriefView:
    recipient: RecipientView
    close_ones: tuple[CloseOneView, ...] = ()
    recollections: tuple[RecollectionView, ...] = ()
    occasion: str = ""
    genre: str = ""
    tone: str = ""
    extension: str = ""
    dedication: str = ""
    banned_novel: tuple[BannedEntryView, ...] = ()
    plot_wishes: tuple[str, ...] = ()
    accepted_extracted_facts: tuple[ExtractedFactView, ...] = ()

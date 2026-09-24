"""Las tools de entrega del writer y del editor: `submit_chapter` y `submit_review`, con sus
campos narrativos para el hook de policy (`architecture.md` §7.4, §7.5; 011-C13, 011-C15).

La revisión solo puede citar lo que existe en la candidata: personajes, lugares, hechos y beats
del capítulo. Citar otra cosa es un error de schema que vuelve al editor (§8.3)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from story_maker.agents.tools import ToolSpec
from story_maker.store.models import Character, Fact, OutlineChapter, Place
from story_maker.validators.chapter_rubric import ChapterReview

SUBMIT_CHAPTER = "submit_chapter"
SUBMIT_REVIEW = "submit_review"


class ChapterSubmission(BaseModel):
    title: str = Field(min_length=1)
    text: str = Field(min_length=1)


def submit_chapter_tool() -> ToolSpec:
    return ToolSpec(
        name=SUBMIT_CHAPTER,
        model=ChapterSubmission,
        description="Entrega el título y el texto del capítulo.",
        narrative=("title", "text"),
    )


@dataclass(frozen=True)
class Citable:
    """Lo que una revisión del capítulo `chapter` de la candidata puede citar (011-I11)."""

    characters: frozenset[int]
    places: frozenset[int]
    facts: frozenset[int]
    beats: frozenset[int]

    def errors(self, review: ChapterReview) -> list[str]:
        errors = [f"el hecho {f} no existe" for f in review.fact_usages if f not in self.facts]
        for i, event in enumerate(review.events):
            cited = [p.character_id for p in event.present]
            if event.excluded_character_id is not None:
                cited.append(event.excluded_character_id)
            errors += [
                f"events[{i}]: el personaje {c} no existe"
                for c in cited
                if c not in self.characters
            ]
            if event.place_id not in self.places:
                errors.append(f"events[{i}]: el lugar {event.place_id} no existe")
            if event.beat not in self.beats:
                errors.append(f"events[{i}]: el beat {event.beat} no es de este capítulo")
        return errors


def citable(session: Session, version_id: int, chapter: int) -> Citable:
    def ids(model: type[Character] | type[Place] | type[Fact]) -> frozenset[int]:
        rows = session.query(model.id).filter(model.version_id == version_id)
        return frozenset(row[0] for row in rows)

    outline = (
        session.query(OutlineChapter)
        .filter(OutlineChapter.version_id == version_id, OutlineChapter.number == chapter)
        .one_or_none()
    )
    beats = outline.beats if outline is not None and isinstance(outline.beats, list) else []
    return Citable(
        characters=ids(Character),
        places=ids(Place),
        facts=ids(Fact),
        beats=frozenset(int(beat["number"]) for beat in beats),
    )


def submit_review_tool(known: Citable) -> ToolSpec:
    """La tool del editor con la comprobación de citas de esta candidata y este capítulo."""

    class CandidateReview(ChapterReview):
        @model_validator(mode="after")
        def _cites_only_what_exists(self) -> Self:
            errors = known.errors(self)
            if errors:
                raise ValueError("; ".join(errors))
            return self

    return ToolSpec(
        name=SUBMIT_REVIEW,
        model=CandidateReview,
        description="Entrega la revisión del capítulo con la rúbrica de capítulo.",
        narrative=("summary", "events[].statement"),
    )

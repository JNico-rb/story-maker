"""Lo común a las pruebas de `revision-visual` (017): la candidata de 017-C01 sobre la del gate
(`at_gate`), su estructura esperada y entregas del doble del revisor visual."""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence
from typing import Any

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import NOW, USAGE, Seed, text_of

from story_maker.agents.fake import Call, Say, Script, Step
from story_maker.pipeline.acceptance import chapter_hash
from story_maker.store.models import Brief, Chapter, Event, Fact, FactUsage, Novel, Place
from story_maker.validators.visual_review import (
    ExpectedChapter,
    ExpectedCover,
    ExpectedEntity,
    ExpectedStructure,
)

TITLE = "El faro de Marta"
DEDICATION = "Para Marta, con cariño"
VILLAVERDE = "Villaverde"


def first_sentence(number: int) -> str:
    return f"Empieza el capítulo {number} junto al mar."


def chapter_text(number: int) -> str:
    return f"{first_sentence(number)}\n\n{text_of(1240)}"


def chapter_title(number: int) -> str:
    return f"Capítulo {number}"


def seed_visual(session_factory: sessionmaker[Session], seed: Seed) -> int:
    """La candidata de 017-C01 sobre la de `at_gate`: título, dedicatoria, capítulos con una
    primera frase propia, Toby en los capítulos 2 y 5, el faro en el 1, Marta en todos y el lugar
    «Villaverde» con un evento registrado en el 3. Devuelve el id de Villaverde."""
    with session_factory() as session:
        novel = session.get_one(Novel, seed.novel_id)
        novel.title = TITLE
        brief = session.query(Brief).filter(Brief.novel_id == seed.novel_id).one()
        brief.content = {"dedication": DEDICATION}
        for chapter in session.query(Chapter).filter(Chapter.version_id == seed.version_id):
            chapter.text = chapter_text(chapter.number)
            chapter.content_hash = chapter_hash(chapter.title, chapter.text)
        use(session, seed.facts["marta"], range(1, 11))
        use(session, seed.facts["toby"], (2, 5))
        use(session, seed.facts["faro"], (1,))
        place = Place(
            version_id=seed.version_id, canonical_name=VILLAVERDE, description="", origin="brief"
        )
        session.add(place)
        session.flush()
        record_event(session, seed.version_id, place.id, 3)
        session.commit()
        return place.id


def use(session: Session, fact_id: int, chapters: Sequence[int]) -> None:
    for chapter in chapters:
        session.add(FactUsage(fact_id=fact_id, chapter=chapter))


def record_event(session: Session, version_id: int, place_id: int, chapter: int) -> None:
    session.add(
        Event(
            version_id=version_id,
            statement=f"algo ocurre en el capítulo {chapter}",
            moment=dt.datetime(2031, 5, 1, 10, 0),
            place_id=place_id,
            type="ordinary",
            analepsis=False,
            origin="recorded",
            chapter=chapter,
            beat=1,
        )
    )


def add_place(session_factory: sessionmaker[Session], version_id: int, name: str) -> int:
    """Un lugar de la story bible sin ningún uso ni evento: sin capítulo en la ficha."""
    with session_factory() as session:
        place = Place(version_id=version_id, canonical_name=name, description="", origin="brief")
        session.add(place)
        session.commit()
        return place.id


def set_chapter_text(
    session_factory: sessionmaker[Session], version_id: int, number: int, text: str
) -> None:
    with session_factory() as session:
        chapter = (
            session.query(Chapter)
            .filter(Chapter.version_id == version_id, Chapter.number == number)
            .one()
        )
        chapter.text = text
        chapter.content_hash = chapter_hash(chapter.title, text)
        session.commit()


def drop_usages(session_factory: sessionmaker[Session], fact_id: int) -> None:
    with session_factory() as session:
        session.query(FactUsage).filter(FactUsage.fact_id == fact_id).delete()
        session.commit()


def name_fact(session: Session, version_id: int, character_id: int) -> Fact:
    return (
        session.query(Fact)
        .filter(
            Fact.version_id == version_id,
            Fact.character_id == character_id,
            Fact.attribute == "name",
        )
        .one()
    )


# --- La estructura esperada de 017-C01, sin base de datos ---------------------------------------

EXPECTED = ExpectedStructure(
    cover=ExpectedCover(TITLE, "Marta", DEDICATION),
    index=tuple(range(1, 11)),
    chapters=tuple(ExpectedChapter(n, chapter_title(n), chapter_text(n)) for n in range(1, 11)),
    ficha=(
        ExpectedEntity("Marta", "personaje", frozenset(range(1, 11))),
        ExpectedEntity("Toby", "personaje", frozenset({2, 5})),
        ExpectedEntity("Faro de Cabo Mayor", "lugar", frozenset({1})),
        ExpectedEntity(VILLAVERDE, "lugar", frozenset({3})),
    ),
)


def chapter_link(number: int) -> dict[str, Any]:
    return {"destination": f"capitulo-{number}"}


def faithful(expected: ExpectedStructure = EXPECTED) -> dict[str, Any]:
    """Una entrega que observa exactamente lo esperado."""
    cover = expected.cover
    return {
        "portada": {
            "title": cover.title,
            "recipient": cover.recipient,
            "dedication": cover.dedication,
        },
        "indice": [
            {"text": f"{n}. {chapter_title(n)}", "destination": f"capitulo-{n}"}
            for n in expected.index
        ],
        "capitulos": [
            {"number": c.number, "title": c.title, "first_sentence": first_sentence(c.number)}
            for c in expected.chapters
        ],
        "ficha": [
            {"name": e.name, "links": [chapter_link(n) for n in sorted(e.chapters)]}
            for e in expected.ficha
        ],
    }


EMPTY: dict[str, Any] = {"portada": {}, "indice": [], "capitulos": [], "ficha": []}


def reviewer_script(*deliveries: dict[str, Any], steps: Sequence[Step] = ()) -> Script:
    """Una sesión del revisor visual que navega y entrega cada `deliveries`, en orden."""
    calls = tuple(Call("submit_visual_review", d) for d in deliveries)
    return Script(steps=(*steps, *calls, Say("Fin.")), usage=USAGE, sdk_cost_usd=0.1)


__all__ = ["NOW"]

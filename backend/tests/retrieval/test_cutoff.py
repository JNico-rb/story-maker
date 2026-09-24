"""016-C10: corte temporal antes de puntuar."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from story_maker.retrieval.fake import FixedVectors
from story_maker.retrieval.retriever import retrieve


def test_each_entity_gives_only_its_latest_card_up_to_the_chapter(
    canon: Any, session_factory: sessionmaker[Session], embedder: FixedVectors
) -> None:
    version = canon.version()
    dog = canon.character(version, "Toby")
    place = canon.place(version, "el puerto nuevo")
    dog_from_1 = canon.card(version, "Toby, el perro.", character=dog, from_chapter=1)
    dog_from_4 = canon.card(version, "Toby, el perro, en el puerto.", character=dog, from_chapter=4)
    place_from_6 = canon.card(version, "El puerto nuevo.", place=place, from_chapter=6)

    def retrieved(chapter: int) -> list[int]:
        with session_factory() as session:
            cards = retrieve(session, version, chapter, ["el perro"], 10, embedder)
            return [card.id for card in cards]

    assert sorted(retrieved(3)) == [dog_from_1]
    assert sorted(retrieved(4)) == [dog_from_4]
    assert sorted(retrieved(6)) == sorted([dog_from_4, place_from_6])

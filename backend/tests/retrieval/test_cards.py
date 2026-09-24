"""016-C1 a 016-C6: plantilla, cadena de cada entidad y sincronización con la story bible."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from story_maker.retrieval.fake import FixedVectors
from story_maker.store.brief_canon import (
    BriefCloseOne,
    BriefRecipient,
    BriefRecollection,
    BriefTrait,
    ConfirmedBrief,
)
from story_maker.store.models import CanonCard, Character, Embedding, Place

BRIEF = ConfirmedBrief(
    recipient=BriefRecipient(
        name="Marta",
        age=40,
        name_element_id=1,
        traits=(BriefTrait("curiosa", element_id=2, mandatory=False),),
    ),
    close_ones=(BriefCloseOne("Toby", "perro", "animal", element_id=3, mandatory=True),),
    recollections=(
        BriefRecollection(
            "se perdió en la feria", "la feria del pueblo", element_id=4, mandatory=True, age=8
        ),
    ),
)


def entity_name(session: Session, card: CanonCard) -> str:
    if card.character_id is not None:
        character = session.get(Character, card.character_id)
        assert character is not None
        return character.canonical_name
    if card.place_id is not None:
        place = session.get(Place, card.place_id)
        assert place is not None
        return place.canonical_name
    return "mundo"


def chains(
    session_factory: sessionmaker[Session], canon: Any, version: int
) -> dict[str, list[int]]:
    """Entidad → los `desde_capitulo` de sus tarjetas, en orden."""
    out: dict[str, list[int]] = {}
    with session_factory() as session:
        for card in canon.cards(version):
            out.setdefault(entity_name(session, card), []).append(card.from_chapter)
    return {name: sorted(chapters) for name, chapters in out.items()}


@pytest.fixture
def planned(canon: Any) -> dict[str, Any]:
    """016-C1: story bible y outline recién aplicados, sin ningún capítulo aceptado."""
    version = canon.candidate(BRIEF)
    canon.world(version)
    marta, _ = canon.named(version, "Marta")
    nia = canon.character(version, "Nia", species="artificial")
    port = canon.place(version, "el puerto nuevo")
    canon.character(version, "Olvido")
    for number in range(1, 11):
        beats: list[Any] = [
            {"description": f"Marta vive el capítulo {number}.", "characters": [marta]}
        ]
        if number == 4:
            beats.append({"description": "Nia se presenta.", "characters": [nia]})
        canon.outline_chapter(version, number, beats)
    canon.event(version, "Marta llega al puerto nuevo.", port, origin="planned", chapter=2, beat=1)
    return {"version": version, "marta": marta, "nia": nia, "port": port}


def test_the_initial_cards_start_where_each_entity_first_appears(
    canon: Any, session_factory: sessionmaker[Session], planned: dict[str, Any]
) -> None:
    version = planned["version"]
    counting = FixedVectors()

    canon.sync(version, counting)

    assert chains(session_factory, canon, version) == {
        "Marta": [1],
        "Toby": [1],
        "la feria del pueblo": [1],
        "mundo": [1],
        "Nia": [4],
        "el puerto nuevo": [2],
    }
    with session_factory() as session:
        vectors = set(session.execute(select(Embedding.content_hash, Embedding.model)).tuples())
    assert {(card.content_hash, "modelo-a") for card in canon.cards(version)} <= vectors
    assert {model for model, _ in counting.embedded} == {"modelo-a"}

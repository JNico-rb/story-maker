"""016-C1 a 016-C6: plantilla, cadena de cada entidad y sincronización con la story bible."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from story_maker.retrieval.fake import FixedVectors
from story_maker.retrieval.retriever import eligible_cards
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


TWO_RECOLLECTIONS = ConfirmedBrief(
    recipient=BriefRecipient(name="Marta", age=40, name_element_id=1, traits=()),
    close_ones=(BriefCloseOne("Rosa", "abuela", "person", element_id=2, mandatory=False),),
    recollections=(
        BriefRecollection(
            "se perdió en la feria", "la feria del pueblo", element_id=3, mandatory=True, age=8
        ),
        BriefRecollection(
            "la abuela Rosa se marchó para siempre",
            "la estación",
            element_id=4,
            mandatory=False,
            age=12,
            present=("Rosa",),
            excluded="Rosa",
        ),
    ),
)
RECORDED = "Marta encuentra una carta en el faro."
PLANNED = "Marta vuelve al faro de noche."
CHAPTER_TEXT = "Las gaviotas chillaban sobre el espigón."
CHAPTER_SUMMARY = "Resumen: la carta cambia el rumbo del viaje."


def current_texts(
    session_factory: sessionmaker[Session], version: int, chapter: int
) -> dict[str, str]:
    """Entidad → texto de su tarjeta vigente en el capítulo."""
    with session_factory() as session:
        return {
            entity_name(session, card): card.text
            for card in eligible_cards(session, version, chapter)
        }


def event_line(text: str, statement: str) -> str:
    """La única línea de evento de la tarjeta con ese enunciado."""
    lines = [line for line in text.splitlines() if statement in line and "presentes:" in line]
    assert len(lines) == 1, (statement, text)
    return lines[0]


def test_a_card_says_what_the_story_bible_knows_before_its_chapter(
    canon: Any, session_factory: sessionmaker[Session]
) -> None:
    version = canon.candidate(TWO_RECOLLECTIONS)
    marta, _ = canon.named(version, "Marta")
    lighthouse = canon.place(version, "el faro", "Un faro blanco sobre el acantilado.")
    canon.world(
        version,
        "Las máquinas aprendieron a soñar.",
        ("Nadie duerme solo.", "Los sueños se comparten.", "Las noches son más largas."),
    )
    canon.fact(version, "energía", "solar")
    canon.event(version, RECORDED, lighthouse, origin="recorded", chapter=2, present=[marta])
    canon.event(version, PLANNED, lighthouse, origin="planned", chapter=5, beat=1, present=[marta])
    canon.chapter(version, 2, CHAPTER_TEXT, CHAPTER_SUMMARY)

    canon.sync(version)

    in_3, in_2 = (
        current_texts(session_factory, version, 3),
        current_texts(session_factory, version, 2),
    )
    marta_3 = in_3["Marta"]
    for fragment in ("Marta", "destinatario", "persona", "1986-01-01"):
        assert fragment in marta_3
    for value in ("Marta", "se perdió en la feria", "la abuela Rosa se marchó para siempre"):
        assert value in marta_3
    feria = event_line(marta_3, "se perdió en la feria")
    assert "la feria del pueblo" in feria
    assert "Marta" in feria
    recorded = event_line(marta_3, RECORDED)
    for fragment in ("2026-05-01 12:00", "el faro", "Marta"):
        assert fragment in recorded
    assert RECORDED not in in_2["Marta"]
    goodbye = event_line(in_3["Rosa"], "la abuela Rosa se marchó para siempre")
    assert "excluyente" in goodbye
    assert "Rosa" in goodbye
    assert "Un faro blanco sobre el acantilado." in in_3["el faro"]
    assert RECORDED in in_3["el faro"]
    for fragment in (
        "Las máquinas aprendieron a soñar.",
        "Nadie duerme solo.",
        "Los sueños se comparten.",
        "Las noches son más largas.",
        "energía: solar",
    ):
        assert fragment in in_3["mundo"]
    for card in canon.cards(version):
        for forbidden in (PLANNED, CHAPTER_TEXT, CHAPTER_SUMMARY):
            assert forbidden not in card.text

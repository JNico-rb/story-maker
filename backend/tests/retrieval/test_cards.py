"""016-C1 a 016-C6: plantilla, cadena de cada entidad y sincronización con la story bible."""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from story_maker.retrieval.fake import FixedVectors
from story_maker.retrieval.retriever import eligible_cards
from story_maker.store.brief_canon import (
    BriefCloseOne,
    BriefRecipient,
    BriefRecollection,
    ConfirmedBrief,
)
from story_maker.store.models import CanonCard, Character, Embedding, Fact, Place
from story_maker.store.session import unit_of_work
from story_maker.store.story_bible import change_fact_value
from story_maker.store.version_copy import copy_version
from story_maker.store.versions import publish

NOW = dt.datetime(2026, 9, 24, 13, 0)


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


def snapshot(canon: Any, version: int) -> dict[int, tuple[int, str, str]]:
    """Tarjeta → (`desde_capitulo`, texto, huella)."""
    return {c.id: (c.from_chapter, c.text, c.content_hash) for c in canon.cards(version)}


def test_accepting_a_chapter_adds_successors_only_where_something_changes(
    canon: Any, session_factory: sessionmaker[Session], planned: dict[str, Any]
) -> None:
    version = planned["version"]
    canon.sync(version)
    before = snapshot(canon, version)
    toby, _ = canon.named(version, "Toby")
    _, fair = canon.named(version, "la feria del pueblo")
    with session_factory() as session:
        trait = session.scalars(
            select(Fact).where(Fact.character_id == planned["marta"], Fact.attribute == "trait")
        ).one()
    canon.chapter(version, 3, "Toby corre por la feria.")
    canon.event(
        version, "Toby vuelve a la feria.", fair, origin="recorded", chapter=3, present=[toby]
    )
    canon.usage(trait.id, 3)

    canon.sync(version)

    after = snapshot(canon, version)
    assert {card: after[card] for card in before} == before
    new = {card: after[card] for card in set(after) - set(before)}
    with session_factory() as session:
        born = {
            entity_name(session, card): card.from_chapter
            for card in canon.cards(version)
            if card.id in new
        }
    assert born == {"Toby": 4, "la feria del pueblo": 4}
    assert all("Toby vuelve a la feria." in text for _, text, _ in new.values())


def test_an_entity_recorded_before_its_planned_chapter_starts_after_that_chapter(
    canon: Any, session_factory: sessionmaker[Session], planned: dict[str, Any]
) -> None:
    version, nia = planned["version"], planned["nia"]
    canon.sync(version)
    early = "Nia saluda a Marta en el puerto nuevo."
    canon.chapter(version, 2, "Una voz nueva en el puerto.")
    canon.event(version, early, planned["port"], origin="recorded", chapter=2, present=[nia])

    canon.sync(version)

    nia_cards = [card for card in canon.cards(version) if card.character_id == nia]
    assert min(card.from_chapter for card in nia_cards) == 3
    with session_factory() as session:
        for chapter in range(3, 12):
            current = [
                c for c in eligible_cards(session, version, chapter) if c.character_id == nia
            ]
            assert len(current) == 1
            assert early in current[0].text
        assert not [c for c in eligible_cards(session, version, 2) if c.character_id == nia]


def test_accepting_a_chapter_again_replaces_what_its_old_version_left_in_later_cards(
    canon: Any, planned: dict[str, Any]
) -> None:
    version = planned["version"]
    toby, _ = canon.named(version, "Toby")
    _, fair = canon.named(version, "la feria del pueblo")
    for number in range(1, 11):
        canon.chapter(version, number, f"Texto del capítulo {number}.")
    first_take = canon.event(
        version, "Toby se escapa en la feria.", fair, origin="recorded", chapter=3, present=[toby]
    )
    canon.event(
        version, "Toby duerme en la feria.", fair, origin="recorded", chapter=5, present=[toby]
    )
    canon.sync(version)
    before = snapshot(canon, version)

    canon.delete_event(first_take)
    canon.event(
        version,
        "Toby gana un premio en la feria.",
        fair,
        origin="recorded",
        chapter=3,
        present=[toby],
    )
    canon.sync(version)

    dog_later = [c for c in canon.cards(version) if c.character_id == toby and c.from_chapter >= 4]
    assert sorted(c.from_chapter for c in dog_later) == [4, 6]
    assert all("Toby gana un premio en la feria." in c.text for c in dog_later)
    assert not any("Toby se escapa en la feria." in c.text for c in dog_later)
    after = snapshot(canon, version)
    assert {card: v for card, v in before.items() if v[0] <= 3} == {
        card: v for card, v in after.items() if v[0] <= 3
    }


def texts_by_entity(
    session_factory: sessionmaker[Session], canon: Any, version: int
) -> dict[tuple[str, int], str]:
    with session_factory() as session:
        return {
            (entity_name(session, card), card.from_chapter): card.text
            for card in canon.cards(version)
        }


def test_a_changed_fact_rebuilds_the_cards_of_its_entity_and_nothing_else(
    canon: Any, session_factory: sessionmaker[Session], planned: dict[str, Any]
) -> None:
    base = planned["version"]
    toby, _ = canon.named(base, "Toby")
    statement = "El perro corre por el puerto nuevo."
    canon.chapter(base, 3, "Carreras en el puerto.")
    canon.event(base, statement, planned["port"], origin="recorded", chapter=3, present=[toby])
    canon.sync(base)
    with unit_of_work(session_factory) as uow:
        publish(uow, base, pdf_path="v1.pdf", now=NOW)
    base_before = snapshot(canon, base)
    with unit_of_work(session_factory) as uow:
        candidate = copy_version(uow, base, now=NOW).version.id
    before = texts_by_entity(session_factory, canon, candidate)
    with unit_of_work(session_factory) as uow:
        dog, _ = canon.named(candidate, "Toby")
        name = uow.session.scalars(
            select(Fact).where(Fact.character_id == dog, Fact.attribute == "name")
        ).one()
        change_fact_value(uow, name.id, "Nala")

    canon.sync(candidate)

    after = texts_by_entity(session_factory, canon, candidate)
    dog_cards = [text for (entity, _), text in after.items() if entity == "Nala"]
    assert dog_cards
    assert all("Personaje: Nala" in t and "name: Nala" in t and "Toby" not in t for t in dog_cards)
    port_lines = [
        line
        for (entity, _), text in after.items()
        if entity == "el puerto nuevo"
        for line in text.splitlines()
        if statement in line
    ]
    assert port_lines
    assert all("presentes: Nala" in line for line in port_lines)
    unrelated = {key for key in before if key[0] not in ("Toby", "el puerto nuevo")}
    assert {key: after[key] for key in unrelated} == {key: before[key] for key in unrelated}
    assert snapshot(canon, base) == base_before

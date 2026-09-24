"""016-C7 y 016-C8: un vector por (huella, modelo de la novela), compartido y de solo
inserción."""

from __future__ import annotations

import dataclasses
import datetime as dt
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from story_maker.config import load_config
from story_maker.retrieval.fake import FixedVectors
from story_maker.retrieval.queries import retrieve_for_editor, retrieve_for_writer
from story_maker.retrieval.vectors import fingerprint, store_vectors
from story_maker.settings import ROOT
from story_maker.store.models import CanonCard, Embedding, Fact
from story_maker.store.session import unit_of_work
from story_maker.store.story_bible import change_fact_value
from story_maker.store.version_copy import copy_version
from story_maker.store.versions import publish

NOW = dt.datetime(2026, 9, 24, 13, 0)
TOBY = "Toby, el perro de la familia, duerme junto a la estufa."
FARO = "El faro del puerto, apagado desde la tormenta."


def stored_vectors(session_factory: sessionmaker[Session]) -> dict[tuple[str, str], bytes]:
    with session_factory() as session:
        rows = session.scalars(select(Embedding)).all()
        return {(row.content_hash, row.model): row.vector for row in rows}


def test_a_card_of_another_novel_with_the_same_text_reuses_the_vector_without_calling_the_model(
    canon: Any, session_factory: sessionmaker[Session]
) -> None:
    first, second = canon.version("modelo-a"), canon.version("modelo-a")
    canon.card(first, TOBY)
    counting = FixedVectors()

    canon.card(second, TOBY, embedder=counting)

    assert counting.embedded == []
    assert list(stored_vectors(session_factory)) == [(fingerprint(TOBY), "modelo-a")]


def test_each_new_text_is_embedded_exactly_once(
    canon: Any, session_factory: sessionmaker[Session]
) -> None:
    version = canon.version("modelo-a")
    counting = FixedVectors()
    with unit_of_work(session_factory) as uow:
        cards = [
            CanonCard(
                version_id=version,
                entity_type="world",
                from_chapter=chapter,
                text=text,
                content_hash=fingerprint(text),
            )
            for chapter, text in ((1, TOBY), (2, TOBY), (3, FARO))
        ]
        for card in cards:
            uow.add(card)
        store_vectors(uow, cards, counting)

    assert sorted(counting.embedded) == sorted([("modelo-a", TOBY), ("modelo-a", FARO)])
    assert set(stored_vectors(session_factory)) == {
        (fingerprint(TOBY), "modelo-a"),
        (fingerprint(FARO), "modelo-a"),
    }


def test_retiring_a_card_keeps_its_vector_and_no_vector_ever_changes(
    canon: Any, session_factory: sessionmaker[Session]
) -> None:
    version = canon.version("modelo-a")
    card_id = canon.card(version, TOBY)
    before = stored_vectors(session_factory)
    assert before
    with unit_of_work(session_factory) as uow:
        uow.delete(uow.session.get(CanonCard, card_id))
    assert stored_vectors(session_factory) == before

    other = FixedVectors({TOBY: (0.0, 1.0)})
    canon.card(version, TOBY, from_chapter=2, embedder=other)

    assert other.embedded == []
    assert stored_vectors(session_factory) == before


def test_cards_and_queries_use_the_model_of_their_novel_and_never_the_config(
    canon: Any, session_factory: sessionmaker[Session]
) -> None:
    config = dataclasses.replace(load_config(ROOT / "config.json"), embedding_model="modelo-b")
    created_before = canon.version("modelo-a")
    created_after = canon.version(config.embedding_model)
    doubles = {created_before: FixedVectors(), created_after: FixedVectors()}
    for version, double in doubles.items():
        canon.card(version, TOBY, character=canon.character(version, "Toby"), embedder=double)
        canon.outline_chapter(version, 1, ["Toby ladra en el patio."])
        with session_factory() as session:
            retrieve_for_writer(session, version, 1, config.top_k, double)
            retrieve_for_editor(session, version, 1, "Toby ladra.", config.top_k, double)

    assert {model for model, _ in doubles[created_before].embedded} == {"modelo-a"}
    assert {model for model, _ in doubles[created_after].embedded} == {"modelo-b"}
    assert len(doubles[created_before].embedded) == 3
    assert set(stored_vectors(session_factory)) == {
        (fingerprint(TOBY), "modelo-a"),
        (fingerprint(TOBY), "modelo-b"),
    }


def test_syncing_a_copy_writes_nothing_and_a_known_text_never_calls_the_model_again(
    canon: Any, session_factory: sessionmaker[Session], planned: dict[str, Any]
) -> None:
    base = planned["version"]
    canon.sync(base)
    with unit_of_work(session_factory) as uow:
        publish(uow, base, pdf_path="v1.pdf", now=NOW)
    with unit_of_work(session_factory) as uow:
        candidate = copy_version(uow, base, now=NOW).version.id
    counting = FixedVectors()
    copied = [(c.id, c.from_chapter, c.text, c.content_hash) for c in canon.cards(candidate)]

    canon.sync(candidate, counting)

    assert [
        (c.id, c.from_chapter, c.text, c.content_hash) for c in canon.cards(candidate)
    ] == copied
    assert counting.embedded == []

    only_world = canon.version("modelo-a")
    canon.world(only_world)
    canon.sync(only_world, counting)

    assert [card.text for card in canon.cards(only_world)] == [
        text for _, _, text, _ in copied if text.startswith("Mundo")
    ]
    assert counting.embedded == []

    vectors_before = stored_vectors(session_factory)
    with unit_of_work(session_factory) as uow:
        marta, _ = canon.named(candidate, "Marta")
        trait = uow.session.scalars(
            select(Fact).where(Fact.character_id == marta, Fact.attribute == "trait")
        ).one()
        change_fact_value(uow, trait.id, "valiente")
    retired = [c for c in canon.cards(candidate) if c.character_id == marta]

    canon.sync(candidate, counting)

    replacement = [c for c in canon.cards(candidate) if c.character_id == marta]
    assert [c.id for c in replacement] != [c.id for c in retired]
    assert counting.embedded == [("modelo-a", card.text) for card in replacement]
    after = stored_vectors(session_factory)
    assert {key: after[key] for key in vectors_before} == vectors_before
    assert all((card.content_hash, "modelo-a") in after for card in retired)

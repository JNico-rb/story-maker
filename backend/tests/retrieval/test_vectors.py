"""016-C7 (la parte de los vectores) y 016-C8: un vector por (huella, modelo de la novela),
compartido y de solo inserción. La sincronización de una copia (primer punto de C7) espera a la
009."""

from __future__ import annotations

import dataclasses
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from story_maker.config import load_config
from story_maker.retrieval.fake import FixedVectors
from story_maker.retrieval.queries import retrieve_for_editor, retrieve_for_writer
from story_maker.retrieval.vectors import fingerprint, store_vectors
from story_maker.settings import ROOT
from story_maker.store.models import CanonCard, Embedding
from story_maker.store.session import unit_of_work

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

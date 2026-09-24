"""016-C17 a 016-C19: las consultas del writer y del editor, y `top_k` por rol."""

from __future__ import annotations

import dataclasses
from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker

from story_maker.config import load_config
from story_maker.retrieval.fake import FixedVectors
from story_maker.retrieval.queries import (
    prospective_query,
    retrieve_for_editor,
    retrieve_for_writer,
    retrospective_query,
)
from story_maker.retrieval.retriever import rank_cards
from story_maker.settings import ROOT

TOP_K = {"writer": 1, "editor": 1}


@pytest.fixture
def lighthouse_and_market(canon: Any) -> dict[str, Any]:
    """El faro solo lo nombra un evento planificado de los beats del 5; el mercado, los beats
    del 6 y el texto del capítulo 5. Con vectores iguales, el mercado gana el desempate."""
    version = canon.version()
    market = canon.place(version, "el mercado")
    lighthouse = canon.place(version, "el faro")
    cards = {
        "market": canon.card(version, "El mercado de los sábados.", place=market),
        "lighthouse": canon.card(version, "El faro del cabo.", place=lighthouse),
    }
    canon.outline_chapter(version, 5, ["Marta sale al amanecer.", "Marta sube la cuesta."])
    canon.planned_event(version, 5, 2, "Marta llega al faro.", lighthouse)
    canon.outline_chapter(version, 6, ["Marta pasea por el mercado."])
    canon.chapter(version, 5, "Marta compra pan en el mercado.")
    return {"version": version, "cards": cards}


def test_the_writer_query_comes_from_the_beats_of_its_chapter_and_their_planned_events(
    session_factory: sessionmaker[Session], lighthouse_and_market: dict[str, Any]
) -> None:
    with session_factory() as session:
        query = prospective_query(session, lighthouse_and_market["version"], 5)

    assert query == ["Marta sale al amanecer.", "Marta sube la cuesta.\nMarta llega al faro."]


def test_the_writer_gets_the_card_its_beats_name_in_any_mode(
    session_factory: sessionmaker[Session],
    lighthouse_and_market: dict[str, Any],
    embedder: FixedVectors,
) -> None:
    with session_factory() as session:
        cards = retrieve_for_writer(session, lighthouse_and_market["version"], 5, TOP_K, embedder)

    assert [card.id for card in cards] == [lighthouse_and_market["cards"]["lighthouse"]]


def test_the_editor_query_has_one_fragment_per_paragraph() -> None:
    text = "Marta compra pan.\n\nLuego pasea por el mercado.\n\n\n  Y vuelve a casa.\n"

    assert retrospective_query(text) == [
        "Marta compra pan.",
        "Luego pasea por el mercado.",
        "Y vuelve a casa.",
    ]


def test_the_editor_gets_the_card_its_text_names_and_the_writer_another_one(
    session_factory: sessionmaker[Session],
    lighthouse_and_market: dict[str, Any],
    embedder: FixedVectors,
) -> None:
    version, cards = lighthouse_and_market["version"], lighthouse_and_market["cards"]
    text = "Marta madruga.\n\nCompra pan en el mercado."

    with session_factory() as session:
        editor = retrieve_for_editor(session, version, 5, text, TOP_K, embedder)
        writer = retrieve_for_writer(session, version, 5, TOP_K, embedder)
        about_lighthouse = retrieve_for_editor(
            session, version, 5, "Marta mira hacia su faro.", TOP_K, embedder
        )

    assert [card.id for card in editor] == [cards["market"]]
    assert [card.id for card in writer] == [cards["lighthouse"]]
    assert [card.id for card in about_lighthouse] == [cards["lighthouse"]]


def test_each_role_gets_its_own_top_k_and_scarcity_never_fails(
    canon: Any, session_factory: sessionmaker[Session], embedder: FixedVectors
) -> None:
    config = dataclasses.replace(
        load_config(ROOT / "config.json"), top_k={"writer": 2, "editor": 3}
    )
    six = canon.version()
    for index in range(6):
        name = f"Vecina {index}"
        canon.card(six, f"{name} del barrio.", character=canon.character(six, name))
    canon.outline_chapter(six, 1, ["Las vecinas del barrio.", "Una vecina llama."])
    one = canon.version()
    only = canon.card(one, "El mundo.")
    canon.outline_chapter(one, 1, ["Empieza la historia."])
    text = "Las vecinas del barrio.\n\nUna vecina llama."

    with session_factory() as session:
        writer_query = prospective_query(session, six, 1)
        writer_fused = [e.card.id for e in rank_cards(session, six, 1, writer_query, embedder)]
        editor_query = retrospective_query(text)
        editor_fused = [e.card.id for e in rank_cards(session, six, 1, editor_query, embedder)]
        writer_six = retrieve_for_writer(session, six, 1, config.top_k, embedder)
        editor_six = retrieve_for_editor(session, six, 1, text, config.top_k, embedder)
        writer_one = retrieve_for_writer(session, one, 1, config.top_k, embedder)
        editor_one = retrieve_for_editor(session, one, 1, text, config.top_k, embedder)

    assert [card.id for card in writer_six] == writer_fused[:2]
    assert [card.id for card in editor_six] == editor_fused[:3]
    assert [card.id for card in writer_one] == [only]
    assert [card.id for card in editor_one] == [only]

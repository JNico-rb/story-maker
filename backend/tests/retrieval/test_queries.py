"""016-C17 a 016-C19: las consultas del writer y del editor, y `top_k` por rol."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker

from story_maker.retrieval.fake import FixedVectors
from story_maker.retrieval.queries import prospective_query, retrieve_for_writer

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

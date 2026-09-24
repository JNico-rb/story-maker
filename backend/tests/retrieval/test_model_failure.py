"""016-C20: sin modelo no hay recuperación a medias ni tarjetas sin vector."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, sessionmaker

from story_maker.retrieval.embedding import EmbeddingError
from story_maker.retrieval.fake import Failure, FixedVectors
from story_maker.retrieval.retriever import retrieve
from story_maker.store.models import CanonCard, Embedding

FAILURES: list[Failure] = ["load", "no_vector"]


@pytest.mark.parametrize("failure", FAILURES)
def test_retrieval_without_the_model_fails_naming_it_and_never_returns_the_lexical_channel(
    canon: Any, session_factory: sessionmaker[Session], failure: Failure
) -> None:
    version = canon.version("modelo-a")
    canon.card(version, "Toby duerme.", character=canon.character(version, "Toby"))

    with session_factory() as session, pytest.raises(EmbeddingError, match="modelo-a"):
        retrieve(session, version, 1, ["Toby"], 5, FixedVectors(fails=failure))


@pytest.mark.parametrize("failure", FAILURES)
def test_writing_a_new_card_without_the_model_fails_and_leaves_no_card_nor_vector(
    canon: Any, session_factory: sessionmaker[Session], failure: Failure
) -> None:
    version = canon.version("modelo-a")

    with pytest.raises(EmbeddingError, match="modelo-a"):
        canon.card(version, "Toby duerme.", embedder=FixedVectors(fails=failure))

    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CanonCard)) == 0
        assert session.scalar(select(func.count()).select_from(Embedding)) == 0
        matches = session.execute(
            text("SELECT rowid FROM canon_cards_fts WHERE canon_cards_fts MATCH 'toby'")
        ).all()
        assert matches == []

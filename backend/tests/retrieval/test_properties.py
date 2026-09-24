"""Invariantes del recuperador con story bibles generadas (`verification.md` §3.4): cada
propiedad se prueba en las dos direcciones."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from typing import Any

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from sqlalchemy.orm import Session, sessionmaker

from story_maker.retrieval.fake import FixedVectors
from story_maker.retrieval.retriever import retrieve

PROPERTY = settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)

WORDS = (
    "faro",
    "tormenta",
    "mercado",
    "perro",
    "árbol",
    "Toby",
    "Nala",
    "puerto",
    "barco",
    "casa",
    "ÁRBOL",
    "Mercado",
)

texts = st.lists(st.sampled_from(WORDS), min_size=1, max_size=5).map(" ".join)
queries = st.lists(texts, min_size=1, max_size=3)


@st.composite
def stories(draw: st.DrawFn) -> list[tuple[str, list[tuple[int, str]]]]:
    """De una a seis entidades (y quizá el mundo), cada una con una cadena de una a tres
    tarjetas con `desde_capitulo` entre 1 y 11."""
    kinds = draw(st.lists(st.sampled_from(["character", "place"]), min_size=1, max_size=6))
    if draw(st.booleans()):
        kinds.append("world")
    story = []
    for kind in kinds:
        chapters = sorted(draw(st.sets(st.integers(1, 11), min_size=1, max_size=3)))
        story.append((kind, [(chapter, draw(texts)) for chapter in chapters]))
    return story


def texts_of(story: list[tuple[str, list[tuple[int, str]]]]) -> list[str]:
    return [text for _, chain in story for _, text in chain]


def vectors_for(values: Iterable[str]) -> FixedVectors:
    """Vectores declarados: uno fijo por texto, derivado de su huella."""
    return FixedVectors(
        {v: tuple(1.0 + b % 7 for b in hashlib.sha256(v.encode()).digest()[:3]) for v in values}
    )


def expected_eligible(
    story: list[tuple[str, list[tuple[int, str]]]], chapter: int
) -> set[tuple[int, int]]:
    """Calculado aparte: por entidad, (su índice, su mayor `desde_capitulo` ≤ `chapter`)."""
    return {
        (index, max(c for c, _ in chain if c <= chapter))
        for index, (_, chain) in enumerate(story)
        if any(c <= chapter for c, _ in chain)
    }


@PROPERTY
@given(story=stories(), query=queries, chapter=st.integers(1, 10), top_k=st.integers(1, 8))
def test_the_same_story_bible_and_query_give_the_same_cards_in_the_same_order(
    canon: Any,
    session_factory: sessionmaker[Session],
    story: list[tuple[str, list[tuple[int, str]]]],
    query: list[str],
    chapter: int,
    top_k: int,
) -> None:
    vectors = vectors_for(texts_of(story) + query)
    first, second = canon.version(), canon.version()
    places = {**canon.story(first, story, vectors), **canon.story(second, story, vectors)}

    def run(version: int) -> list[tuple[int, int]]:
        with session_factory() as session:
            cards = retrieve(session, version, chapter, query, top_k, vectors)
            return [places[card.id] for card in cards]

    assert run(first) == run(first) == run(second)


@PROPERTY
@given(story=stories(), chapter=st.integers(1, 10), data=st.data())
def test_queries_that_match_different_cards_lead_with_different_cards(
    canon: Any,
    session_factory: sessionmaker[Session],
    story: list[tuple[str, list[tuple[int, str]]]],
    chapter: int,
    data: st.DataObject,
) -> None:
    def key(index: int, from_chapter: int) -> str:
        return f"clave{index}x{from_chapter}"

    keyed = [
        (kind, [(c, f"{text} {key(index, c)}") for c, text in chain])
        for index, (kind, chain) in enumerate(story)
    ]
    eligible = expected_eligible(keyed, chapter)
    assume(len(eligible) >= 2)
    x, y = data.draw(
        st.lists(st.sampled_from(sorted(eligible)), min_size=2, max_size=2, unique=True)
    )
    vectors = vectors_for([*texts_of(keyed), key(*x), key(*y)])
    version = canon.version()
    places = canon.story(version, keyed, vectors)

    def first(query: str) -> tuple[int, int]:
        with session_factory() as session:
            return places[retrieve(session, version, chapter, [query], 1, vectors)[0].id]

    assert first(key(*x)) == x
    assert first(key(*y)) == y

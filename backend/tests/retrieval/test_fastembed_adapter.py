"""031-C05: el adaptador de incrustaciones sobre fastembed, con la librería sustituida."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import ClassVar

import pytest

from story_maker.retrieval.embedding import EmbeddingError, embed_texts
from story_maker.retrieval.fastembed_model import FastEmbedModel


class FakeTextEmbedding:
    """Doble de `fastembed.TextEmbedding`: un vector por texto según su longitud."""

    loaded: ClassVar[list[str]] = []

    def __init__(self, model_name: str) -> None:
        FakeTextEmbedding.loaded.append(model_name)

    def embed(self, documents: Iterable[str]) -> Iterator[list[float]]:
        return iter([[float(len(text)), 1.0] for text in documents])


class UnloadableTextEmbedding:
    def __init__(self, model_name: str) -> None:
        raise ValueError(f"{model_name} no está en el catálogo")


class ShortTextEmbedding(FakeTextEmbedding):
    def embed(self, documents: Iterable[str]) -> Iterator[list[float]]:
        return iter([[1.0, 0.0]])


def test_the_adapter_returns_one_vector_per_text_in_order_with_the_given_model() -> None:
    FakeTextEmbedding.loaded = []
    embedder = FastEmbedModel(FakeTextEmbedding)

    vectors = embedder.embed("modelo-a", ["uno", "cuatro", "si"])

    assert vectors == [[3.0, 1.0], [6.0, 1.0], [2.0, 1.0]]
    assert FakeTextEmbedding.loaded == ["modelo-a"]


def test_the_adapter_loads_each_model_once() -> None:
    FakeTextEmbedding.loaded = []
    embedder = FastEmbedModel(FakeTextEmbedding)

    embedder.embed("modelo-a", ["uno"])
    embedder.embed("modelo-a", ["dos"])

    assert FakeTextEmbedding.loaded == ["modelo-a"]


def test_a_model_that_does_not_load_gives_the_embedding_error_naming_it() -> None:
    with pytest.raises(EmbeddingError, match="modelo-a"):
        embed_texts(FastEmbedModel(UnloadableTextEmbedding), "modelo-a", ["uno"])


def test_a_model_that_does_not_return_one_vector_per_text_gives_the_embedding_error() -> None:
    with pytest.raises(EmbeddingError, match="modelo-a"):
        FastEmbedModel(ShortTextEmbedding).embed("modelo-a", ["uno", "dos"])

"""El modelo de incrustación real sobre fastembed, en local (`architecture.md` §6.3).

Cumple `EmbeddingModel`; solo corre en las demostraciones D: las pruebas T le pasan un doble de
la clase de fastembed y usan `retrieval.fake` en el resto.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any, Protocol

from story_maker.retrieval.embedding import EmbeddingError


class TextEmbedding(Protocol):
    def embed(self, documents: Iterable[str]) -> Iterable[Any]: ...


def _fastembed_text_embedding(model_name: str) -> TextEmbedding:
    # Import tardío: fastembed arrastra onnxruntime, que ni las pruebas ni el arranque sin
    # incrustaciones necesitan cargar.
    from fastembed import TextEmbedding as FastEmbedTextEmbedding

    model: TextEmbedding = FastEmbedTextEmbedding(model_name=model_name)
    return model


class FastEmbedModel:
    """Un vector por texto, en orden, con el modelo que recibe; carga cada modelo una vez."""

    def __init__(
        self, text_embedding: Callable[[str], TextEmbedding] = _fastembed_text_embedding
    ) -> None:
        self._text_embedding = text_embedding
        self._loaded: dict[str, TextEmbedding] = {}

    def embed(self, model: str, texts: Sequence[str]) -> list[list[float]]:
        vectors = [[float(x) for x in vector] for vector in self._load(model).embed(list(texts))]
        if len(vectors) != len(texts) or any(len(vector) == 0 for vector in vectors):
            raise EmbeddingError(model, "no devuelve un vector por texto")
        return vectors

    def _load(self, model: str) -> TextEmbedding:
        if model not in self._loaded:
            try:
                self._loaded[model] = self._text_embedding(model)
            except Exception as exc:
                raise EmbeddingError(model, f"no carga ({exc})") from exc
        return self._loaded[model]

"""Puerto del modelo de incrustación y su llamada comprobada (`architecture.md` §6.3, §15.9).

El modelo corre en local y no es un rol: no pasa por el puerto de agente. Las pruebas T usan el
doble de vectores fijos (`retrieval.fake`); el modelo real solo corre en las demostraciones D.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

import sqlite_vec


class EmbeddingError(RuntimeError):
    """El modelo de incrustación no carga o no devuelve vector; el mensaje nombra el modelo."""

    def __init__(self, model: str, detail: str) -> None:
        self.model = model
        super().__init__(f"modelo de incrustación {model!r}: {detail}")


class EmbeddingModel(Protocol):
    def embed(self, model: str, texts: Sequence[str]) -> list[list[float]]:
        """Un vector por texto, en el mismo orden, calculado con `model`."""
        ...


def embed_texts(embedder: EmbeddingModel, model: str, texts: Sequence[str]) -> list[bytes]:
    """Los vectores de `texts` con `model`, serializados para `sqlite-vec`. Sin vector para
    alguno, error explícito: nunca un resultado a medias (§2, premisa 5)."""
    try:
        vectors = embedder.embed(model, texts)
    except EmbeddingError:
        raise
    except Exception as exc:
        raise EmbeddingError(model, f"no carga ({exc})") from exc
    if len(vectors) != len(texts) or any(len(vector) == 0 for vector in vectors):
        raise EmbeddingError(model, "no devuelve un vector por texto")
    return [sqlite_vec.serialize_float32(vector) for vector in vectors]

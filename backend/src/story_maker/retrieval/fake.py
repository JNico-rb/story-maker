"""Doble del modelo de incrustación: los vectores fijos que declara cada prueba (§15.9)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

DEFAULT_VECTOR = (1.0, 0.0)


class FixedVectors:
    """Devuelve el vector declarado para cada texto, o `default`, y apunta cada texto que
    incrusta con su modelo."""

    def __init__(
        self,
        vectors: Mapping[str, Sequence[float]] | None = None,
        *,
        default: Sequence[float] = DEFAULT_VECTOR,
    ) -> None:
        self.vectors = dict(vectors or {})
        self.default = tuple(default)
        self.embedded: list[tuple[str, str]] = []

    def embed(self, model: str, texts: Sequence[str]) -> list[list[float]]:
        self.embedded += [(model, text) for text in texts]
        return [list(self.vectors.get(text, self.default)) for text in texts]

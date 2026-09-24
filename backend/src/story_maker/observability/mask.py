"""Máscara de datos personales: nombres y fechas del brief fuera de lo exportado (`arch.` §13.5)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

PLACEHOLDER_DATE = "[FECHA]"


@dataclass(frozen=True)
class Mask:
    """Sustituye, en cualquier texto, los nombres por `[NOMBRE_n]` y las fechas por `[FECHA]`."""

    names: tuple[str, ...] = ()
    dates: tuple[str, ...] = ()

    @staticmethod
    def empty() -> Mask:
        return Mask()

    def apply(self, text: str) -> str:
        result = text
        for index, name in enumerate(self.names, start=1):
            if name:
                result = result.replace(name, f"[NOMBRE_{index}]")
        for date in self.dates:
            if date:
                result = result.replace(date, PLACEHOLDER_DATE)
        return result

    def apply_to_value(self, value: Any) -> Any:
        """Enmascara recursivamente cualquier texto dentro de listas y diccionarios (004-I1)."""
        if isinstance(value, str):
            return self.apply(value)
        if isinstance(value, Mapping):
            return {key: self.apply_to_value(item) for key, item in value.items()}
        if isinstance(value, Sequence) and not isinstance(value, str | bytes):
            return [self.apply_to_value(item) for item in value]
        return value

    def __or__(self, other: Mask) -> Mask:
        """Unión de dos máscaras: la de una llamada MCP que toca varias novelas (004-C11)."""
        names = self.names + tuple(name for name in other.names if name not in self.names)
        dates = self.dates + tuple(date for date in other.dates if date not in self.dates)
        return Mask(names=names, dates=dates)

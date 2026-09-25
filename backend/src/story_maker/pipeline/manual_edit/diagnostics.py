"""El diagnóstico del lint en vivo y del 422 del guardado (019): tipo, mensaje, posición en
caracteres del texto enviado si señala un fragmento, y si bloqueará el guardado."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

TYPES = (
    "forma_no_canonica",
    "personaje_desconocido",
    "hecho",
    "prohibida",
    "linter",
    "cronologia",
    "longitud",  # solo en el 422 del guardado: el lint no mide la longitud
)


@dataclass(frozen=True)
class Diagnostic:
    type: str
    message: str
    blocking: bool
    start: int | None = None
    end: int | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        body: dict[str, Any] = {"type": self.type, "message": self.message, **self.extra}
        if self.start is not None and self.end is not None:
            body["position"] = {"start": self.start, "end": self.end}
        body["blocking"] = self.blocking
        return body


def ordered(diagnostics: Iterable[Diagnostic]) -> list[Diagnostic]:
    """Por posición; los que no tienen, al final y por tipo. A igual clave, en el orden en que se
    detectaron: así el mismo texto da siempre el mismo orden (019-I2)."""
    return sorted(
        diagnostics,
        key=lambda d: (0, d.start, 0) if d.start is not None else (1, 0, TYPES.index(d.type)),
    )

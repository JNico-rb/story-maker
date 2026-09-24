"""Tipos comunes de los cuatro linters de prosa (`definitions.md` §6, `Defecto`).

Los linters son puros (018-I3): quien los llama traduce esto a `Defecto`/`ResultadoDeValidador`/
`Score` reales y los registra. Estos tipos son solo la salida de un linter, no la del sistema.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Defect:
    """Un aviso no bloqueante de un linter (018-I1): su mensaje y, si aplica, su párrafo."""

    message: str
    paragraph: int | None = None


@dataclass(frozen=True)
class LinterResult:
    """Resultado de un linter: pasa si no da avisos; la métrica es la de la tabla de reglas
    comunes de la spec 018 (número de avisos, índice, densidad...)."""

    validator: str
    passed: bool
    metric: float | None
    defects: tuple[Defect, ...] = field(default_factory=tuple)

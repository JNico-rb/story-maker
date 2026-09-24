"""Resultado de una verificación formal (`definitions.md` §9, §12.4; spec 007).

`ChronologyResult` es el resultado del `FicheroDeCronologia`: `passed`, `failed` o `error`.
`VerifierInterruption` es la ausencia de veredicto, con su motivo de interrupción.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

Invariant = Literal["T1", "T2", "T3", "T4", "T5"]
INVARIANTS: tuple[Invariant, ...] = ("T1", "T2", "T3", "T4", "T5")

FileResult = Literal["passed", "failed", "error"]
InterruptionReason = Literal["verifier_unreachable", "verifier_timeout"]


@dataclass(frozen=True)
class ChronologyResult:
    """`holds` da cumple sí/no de T1 a T5 en `passed` y `failed`, y va vacío en `error`;
    `witnesses`, el primer testigo (ids de fila) de cada invariante violado; `reason`, el motivo
    de un `error`."""

    result: FileResult
    holds: Mapping[Invariant, bool] = field(default_factory=dict)
    witnesses: Mapping[Invariant, tuple[int, ...]] = field(default_factory=dict)
    reason: str | None = None


@dataclass(frozen=True)
class VerifierInterruption:
    """Sin veredicto: la verificación no llegó a darse. `detail` nunca lleva secretos."""

    reason: InterruptionReason
    detail: str = ""


VerificationOutcome = ChronologyResult | VerifierInterruption

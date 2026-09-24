"""Lo que el hook de policy pide al `MotorDePoliticas` y lo que espera de vuelta (§7.5, §12.2).

El motor es de 005-guardarrailes; aquí solo está la forma que usa el puerto de agente."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

Decision = Literal["allow", "deny", "flag"]


@dataclass(frozen=True)
class PolicyField:
    """Un texto de la entrada de la tool, con su ruta; `narrative` si la tool lo marca así."""

    path: str
    value: str
    narrative: bool


@dataclass(frozen=True)
class PolicyRequest:
    origin: str
    user_id: int
    novel_id: int
    run_id: int | None
    role: str
    tool: str
    fields: tuple[PolicyField, ...]


@dataclass(frozen=True)
class PolicyDecision:
    decision: Decision
    reason: str | None = None


class PolicyEngine(Protocol):
    def decide(self, request: PolicyRequest) -> PolicyDecision: ...

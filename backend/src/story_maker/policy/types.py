"""Formas de PeticionDePolitica y DecisionDePolitica (definitions.md §7, architecture.md §12.2)."""

from typing import Literal

from pydantic import BaseModel

NivelProhibida = Literal["global", "user", "novel"]
TipoEntrada = Literal["word", "topic"]
OrigenDecision = Literal[
    "policy_hook", "free_text", "change_request", "manual_edit", "publication_gate", "mcp_write"
]
Decision = Literal["allow", "deny", "flag"]


class EntradaProhibida(BaseModel):
    term: str
    type: TipoEntrada
    level: NivelProhibida
    keywords: list[str] = []
    owner: str | None = None
    """Cliente (nivel user) o novela (nivel novel) propietarios; vacío para global."""


class CampoNarrativo(BaseModel):
    path: str
    narrativo: bool
    texto: str


class PeticionDePolitica(BaseModel):
    origen: OrigenDecision
    cliente: str | None = None
    novela: str | None = None
    ejecucion: str | None = None
    rol: str | None = None
    tool: str | None = None
    campos: list[CampoNarrativo] = []
    banned_entries: list[EntradaProhibida] = []


class DecisionDePolitica(BaseModel):
    decision: Decision
    rule: str | None = None
    detail: list[dict[str, str]] | None = None

"""La selección de una solicitud de cambio: un hecho o un fragmento (versión, capítulo y cita)
(`definitions.md` §5 SolicitudDeCambio)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class FactSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["fact"]
    fact_id: int


class FragmentSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["fragment"]
    version: int
    chapter: int
    quote: str


Selection = Annotated[FactSelection | FragmentSelection, Field(discriminator="type")]

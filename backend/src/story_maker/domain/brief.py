"""Modelo del `Brief` y sus comprobaciones deterministas: schema, faltantes, contradicciones
C1-C6 y cota de obligatorios (`definitions.md` §1, `architecture.md` §3.2,
`domain-knowledge.md` §4.3, §5.2). Puro: sin I/O, opera sobre el contenido ya cargado."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Ocasion = Literal["birthday", "wedding", "anniversary", "retirement", "other"]
Genero = Literal["adventure", "humor", "romance", "mystery", "drama", "fable"]
Tono = Literal["tender", "funny", "exciting", "nostalgic", "epic", "unsettling"]
Extension = Literal["short", "medium", "long"]
FranjaDeEdad = Literal["children", "teen", "adult"]

_CHILDISH_GENRES: tuple[Genero, ...] = ("romance", "drama")
_UNSETTLING_TONE: Tono = "unsettling"
_AGE_GATED_OCCASIONS: tuple[Ocasion, ...] = ("wedding", "anniversary")


class Trait(BaseModel):
    model_config = ConfigDict(extra="forbid")
    statement: str = ""
    mandatory: bool = False


class CloseOne(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = ""
    relation: str = ""
    species: Literal["person", "animal"] | None = None
    age: int | None = Field(default=None, ge=0)
    birth_date: dt.date | None = None
    mandatory: bool = False


class Recollection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    statement: str = ""
    age: int | None = Field(default=None, ge=0)
    year: int | None = None
    place: str = ""
    present: list[str] = Field(default_factory=list)
    excluded: str | None = None
    mandatory: bool = False


class Recipient(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = ""
    age: int | None = Field(default=None, ge=0)
    birth_date: dt.date | None = None
    traits: list[Trait] = Field(default_factory=list)
    relation: str | None = None


class PlotWish(BaseModel):
    model_config = ConfigDict(extra="forbid")
    statement: str = ""


class BriefContent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recipient: Recipient = Field(default_factory=Recipient)
    close_ones: list[CloseOne] = Field(default_factory=list)
    recollections: list[Recollection] = Field(default_factory=list)
    occasion: Ocasion | None = None
    genre: Genero | None = None
    tone: Tono | None = None
    length: Extension | None = None
    dedication: str = ""
    banned_asked: bool = False
    plot_wishes: list[PlotWish] = Field(default_factory=list)


def age_band(age: int) -> FranjaDeEdad:
    """`FranjaDeEdad`: infantil (< 12), juvenil (12-17) o adulto (>= 18) (`definitions.md` §1)."""
    if age < 12:
        return "children"
    if age < 18:
        return "teen"
    return "adult"

"""`revision-visual`: la estructura esperada de la `VistaDeVersion`, lo que entrega el revisor
visual por `submit_visual_review` y la comparación que decide (`architecture.md` §9.4, §11.2;
spec 017).

El modelo navega; no juzga: su entrega solo trae observaciones, sin veredicto, y el resultado lo
calcula el código comparando con la estructura esperada, parte por parte (017-I1). Un defecto de
la parte `ficha` por una entidad sin capítulo es de datos; cualquier discrepancia con lo
observado es de render y nunca lleva capítulo (017-I4). Nada aquí abre una sesión ni lee SQLite."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

VALIDATOR = "revision-visual"

Part = Literal["portada", "indice", "capitulos", "ficha"]
PARTS: tuple[Part, ...] = ("portada", "indice", "capitulos", "ficha")


@dataclass(frozen=True)
class ExpectedCover:
    title: str
    recipient: str
    dedication: str


@dataclass(frozen=True)
class ExpectedChapter:
    number: int
    title: str
    text: str


@dataclass(frozen=True)
class ExpectedEntity:
    """Una entidad de la `FichaDePersonajes` con los capítulos en que aparece (013)."""

    name: str
    kind: str  # "personaje" | "lugar"
    chapters: frozenset[int]


@dataclass(frozen=True)
class ExpectedStructure:
    """Lo que la vista de la candidata debe mostrar, calculado desde SQLite: la *i*-ésima entrada
    del índice lleva al capítulo `index[i]`."""

    cover: ExpectedCover
    index: tuple[int, ...]
    chapters: tuple[ExpectedChapter, ...]
    ficha: tuple[ExpectedEntity, ...]

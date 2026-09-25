"""`revision-visual`: la estructura esperada de la `VistaDeVersion`, lo que entrega el revisor
visual por `submit_visual_review` y la comparación que decide (`architecture.md` §9.4, §11.2;
spec 017).

El modelo navega; no juzga: su entrega solo trae observaciones, sin veredicto, y el resultado lo
calcula el código comparando con la estructura esperada, parte por parte (017-I1). Un defecto de
la parte `ficha` por una entidad sin capítulo es de datos; cualquier discrepancia con lo
observado es de render y nunca lleva capítulo (017-I4). Nada aquí abre una sesión ni lee SQLite."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from story_maker.agents.tools import ToolSpec

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


# --- Lo que entrega el revisor: solo observaciones (017-C12, 017-I1) ----------------------------

SUBMIT_VISUAL_REVIEW = "submit_visual_review"
# El destino de un enlace: la parte de la vista a la que lleva, o ninguna (`null`).
DESTINATION = r"^(portada|indice|ficha|capitulo-[1-9][0-9]*)$"
Destination = Annotated[str, StringConstraints(pattern=DESTINATION)] | None


class _Observation(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CoverObservation(_Observation):
    title: str = ""
    recipient: str = ""
    dedication: str = ""


class IndexEntryObservation(_Observation):
    text: str = ""
    destination: Destination = None


class ChapterObservation(_Observation):
    number: int
    title: str = ""
    first_sentence: str = ""


class LinkObservation(_Observation):
    destination: Destination = None


class EntityObservation(_Observation):
    name: str
    links: list[LinkObservation] = Field(default_factory=list)


class VisualReviewSubmission(_Observation):
    """`submit_visual_review`: las cuatro partes son obligatorias; una parte vacía significa «no lo
    vi» y se compara (017-C12, 017-C13). No hay campo de veredicto (017-I1)."""

    portada: CoverObservation
    indice: list[IndexEntryObservation]
    capitulos: list[ChapterObservation]
    ficha: list[EntityObservation]


def submit_visual_review_tool() -> ToolSpec:
    return ToolSpec(
        name=SUBMIT_VISUAL_REVIEW,
        model=VisualReviewSubmission,
        description="Entrega lo observado en la portada, el índice, los capítulos y la ficha.",
    )


# --- Lo que recibe el revisor: la dirección y la forma, nunca los valores (017-C02, 017-I2) ------


DELIVER: dict[Part, str] = {
    "portada": "el título, el nombre del destinatario y la dedicatoria, tal como se leen",
    "indice": "cada entrada, en orden, con su texto y el destino al que lleva al pulsarla",
    "capitulos": "el número, el título y la primera frase de cada capítulo",
    "ficha": "cada personaje y cada lugar por su nombre, con el destino de cada uno de sus enlaces",
}
DESTINATIONS = (
    "El destino de un enlace es la parte a la que llegas al pulsarlo: `portada`, `indice`, "
    "`ficha` o `capitulo-<n>`; `null` si no lleva a ninguna."
)


def reviewer_message(url: str, expected: ExpectedStructure) -> str:
    """La dirección de la vista y la forma de la entrega: las partes, qué entregar de cada una y
    cuántos capítulos, personajes y lugares hay. Ningún valor que el código compare."""
    kinds = [e.kind for e in expected.ficha]
    structure = {
        "parts": list(PARTS),
        "deliver": dict(DELIVER),
        "destinations": DESTINATIONS,
        "chapters": len(expected.chapters),
        "characters": kinds.count("personaje"),
        "places": kinds.count("lugar"),
    }
    return json.dumps({"url": url, "structure": structure}, ensure_ascii=False, indent=2)


# --- La comparación: el código decide (017-C04 a 017-C13, 017-I1, 017-I4) -----------------------

Kind = Literal["datos", "render"]


@dataclass(frozen=True)
class VisualDefect:
    """Un `Defecto` de `revision-visual`, siempre bloqueante: de datos (parte `ficha`, con el
    capítulo en que sale la entidad o ninguno) o de render (nunca con capítulo)."""

    part: Part
    kind: Kind
    chapter: int | None
    message: str


@dataclass(frozen=True)
class VisualVerdict:
    """El resultado de cada parte evaluada, en orden, y sus defectos."""

    parts: tuple[tuple[Part, bool], ...]
    defects: tuple[VisualDefect, ...]

    @property
    def passed(self) -> bool:
        return all(ok for _, ok in self.parts)


def normalized(text: str) -> str:
    """Espacios colapsados (saltos de línea incluidos) y sin distinguir mayúsculas; las letras,
    los acentos y los signos cuentan (017-C05)."""
    return " ".join(text.split()).casefold()


def texts_match(observed: str, expected: str) -> bool:
    return normalized(observed) == normalized(expected)


def sentence_in(observed: str, text: str) -> bool:
    """Una primera frase observada coincide si está en el texto de su capítulo; vacía, nunca."""
    sentence = normalized(observed)
    return bool(sentence) and sentence in normalized(text)


def compare(expected: ExpectedStructure, observed: VisualReviewSubmission) -> VisualVerdict:
    """Cada parte por separado: una que no pasa no impide evaluar las otras (017-C06)."""
    by_part: dict[Part, tuple[VisualDefect, ...]] = {
        "portada": _cover(expected.cover, observed.portada),
        "indice": _index(expected.index, observed.indice),
        "capitulos": _chapters(expected.chapters, observed.capitulos),
        "ficha": (),
    }
    return VisualVerdict(
        tuple((part, not by_part[part]) for part in PARTS),
        tuple(d for part in PARTS for d in by_part[part]),
    )


def _render(part: Part, message: str) -> VisualDefect:
    return VisualDefect(part, "render", None, message)


def _cover(expected: ExpectedCover, observed: CoverObservation) -> tuple[VisualDefect, ...]:
    fields = (
        ("el título", expected.title, observed.title),
        ("el destinatario", expected.recipient, observed.recipient),
        ("la dedicatoria", expected.dedication, observed.dedication),
    )
    return tuple(
        _render("portada", f"portada: se esperaba {label} «{want}» y se vio «{seen}»")
        for label, want, seen in fields
        if not texts_match(seen, want)
    )


def _index(
    expected: tuple[int, ...], observed: list[IndexEntryObservation]
) -> tuple[VisualDefect, ...]:
    defects: list[VisualDefect] = []
    if len(observed) != len(expected):
        defects.append(
            _render(
                "indice",
                f"índice: se esperaban {len(expected)} entradas y se vieron {len(observed)}",
            )
        )
    for position, (chapter, entry) in enumerate(zip(expected, observed, strict=False), start=1):
        if entry.destination != chapter_destination(chapter):
            defects.append(
                _render(
                    "indice",
                    f"índice: la entrada {position} debe llevar al capítulo {chapter} y lleva a "
                    f"{_where(entry.destination)}",
                )
            )
    return tuple(defects)


def chapter_destination(number: int) -> str:
    return f"capitulo-{number}"


def _where(destination: str | None) -> str:
    return destination if destination is not None else "ninguna parte"


def _chapters(
    expected: tuple[ExpectedChapter, ...], observed: list[ChapterObservation]
) -> tuple[VisualDefect, ...]:
    seen: dict[int, ChapterObservation] = {}
    defects: list[str] = []
    for chapter in observed:
        if chapter.number in seen:
            defects.append(f"el capítulo {chapter.number} se vio dos veces")
        seen.setdefault(chapter.number, chapter)
    for want in expected:
        got = seen.get(want.number)
        if got is None:
            defects.append(f"no se vio el capítulo {want.number}")
            continue
        if not texts_match(got.title, want.title):
            defects.append(
                f"el capítulo {want.number} debe titularse «{want.title}» y se vio «{got.title}»"
            )
        if not sentence_in(got.first_sentence, want.text):
            defects.append(
                f"la primera frase vista en el capítulo {want.number} («{got.first_sentence}») "
                "no está en su texto"
            )
    numbers = {want.number for want in expected}
    defects += [f"se vio un capítulo {n} que no existe" for n in seen if n not in numbers]
    return tuple(_render("capitulos", f"capítulos: {message}") for message in defects)

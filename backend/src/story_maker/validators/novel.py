"""Validadores deterministas de la etapa 1 y traducción del resultado de la etapa 2 de Lean, del
`GateDePublicacion` (012-C3, 012-C5, 012-C9, 012-C10, 012-C11; `architecture.md` §9.4, §11.2).

`elementos-obligatorios` y `palabras-prohibidas` aquí solo miran datos ya estructurados: qué
elemento personal asignó el outline a qué capítulos, qué hechos tienen uso, y el texto de cada
capítulo contra las prohibidas activas. Ninguno lee la cronología ni conoce `FicheroDeCronologia`
(007) — `lean_stage_result` solo traduce lo que 007 ya decidió (`ChronologyResult`,
`formal.defects.defects_from`) a lo que el gate necesita: si el fallo es atribuible, y el motivo
cuando no compila. No corre nada por su cuenta.

Sin acceso a la cola, al worker ni a las ejecuciones (011, todavía fuera de esta rama): las vistas
de entrada las construyen las pruebas directamente, como hace `story_bible_view.py` (010) hasta
que 009 las alimente."""

from __future__ import annotations

from dataclasses import dataclass

from story_maker.formal.defects import Defect
from story_maker.formal.defects import defects_from as lean_defects_from
from story_maker.formal.result import ChronologyResult
from story_maker.policy.types import DecisionDePolitica
from story_maker.store.story_bible import StoryBible

MANDATORY_ELEMENTS_VALIDATOR = "elementos-obligatorios"
BANNED_TERMS_VALIDATOR = "palabras-prohibidas"


@dataclass(frozen=True)
class NovelValidatorResult:
    """Lo que deja cada validador del gate que corre sobre la novela entera (`ResultadoDeValidador`,
    versión mínima de 012: aquí solo `passed` y los defectos; el score completo con Langfuse es
    C24, fuera de este paso)."""

    validator: str
    passed: bool
    defects: tuple[Defect, ...]

    @property
    def score(self) -> float:
        return 1.0 if self.passed else 0.0


# --- elementos-obligatorios (012-C3) -----------------------------------------------------------


@dataclass(frozen=True)
class MandatoryElement:
    """Un `ElementoPersonal` obligatorio, con los capítulos que el outline le asignó."""

    id: str
    label: str
    assigned_chapters: tuple[int, ...]


def mandatory_elements_result(
    elements: tuple[MandatoryElement, ...], used_element_ids: frozenset[str]
) -> NovelValidatorResult:
    """Un elemento sin ningún `UsoDeHecho` (de cualquiera de sus hechos, en cualquier capítulo)
    da un defecto bloqueante por cada capítulo que el outline le asignó (012-C3). Un elemento
    usado en un capítulo que el outline no le asignó también cuenta como usado: la pasada no mira
    dónde, solo si hay uso."""
    defects = tuple(
        Defect(MANDATORY_ELEMENTS_VALIDATOR, None, True, chapter, f"«{element.label}» sin uso")
        for element in elements
        if element.id not in used_element_ids
        for chapter in element.assigned_chapters
    )
    return NovelValidatorResult(MANDATORY_ELEMENTS_VALIDATOR, not defects, defects)


# --- palabras-prohibidas, aplicado a los capítulos (012-C5) ------------------------------------


@dataclass(frozen=True)
class ChapterText:
    chapter: int
    text: str


@dataclass(frozen=True)
class BannedTermMatch:
    """Una coincidencia en un capítulo, o en la portada o la ficha (`location` `cover` o `sheet`,
    sin capítulo: no se puede atribuir, 012-C6)."""

    term: str
    level: str
    variant: str
    chapter: int | None
    location: str = "chapter"


def banned_terms_in_chapters(
    chapters: tuple[ChapterText, ...], matches: tuple[BannedTermMatch, ...]
) -> tuple[NovelValidatorResult, DecisionDePolitica]:
    """`palabras-prohibidas` aplicado a los capítulos de la candidata, con origen
    `publication_gate` (012-C5): un defecto bloqueante por capítulo con coincidencia, y una única
    decisión de política por pasada con todas las coincidencias en el detalle (`deny` si hay
    alguna, `allow` si no hay ninguna). Una coincidencia en la portada o la ficha da un defecto
    sin capítulo, que ninguna reescritura corrige (012-C6).

    `matches` ya viene calculada (`domain.banned_terms.find_term_matches` sobre las tres listas
    activas al correr la pasada): aquí solo se atribuye y se agrega, sin repetir la normalización
    ni la coincidencia por tokens, que son de 005."""
    known_chapters = {c.chapter for c in chapters}
    defects = tuple(
        Defect(BANNED_TERMS_VALIDATOR, None, True, match.chapter, _banned_message(match))
        for match in matches
        if match.chapter in known_chapters or match.location != "chapter"
    )
    detail = [_match_detail(match) for match in matches]
    decision = DecisionDePolitica(
        decision="deny" if detail else "allow",
        rule=BANNED_TERMS_VALIDATOR if detail else None,
        detail=detail or None,
    )
    return NovelValidatorResult(BANNED_TERMS_VALIDATOR, not defects, defects), decision


# --- cronologia-lean, traducción del resultado de 007 a lo que decide el gate (012-C9..C11) -----


@dataclass(frozen=True)
class LeanStageResult:
    """Lo que la etapa 2 necesita del verificador formal (007), más allá de sus propios
    `Defecto`: si algún testigo quedó sin capítulo (no atribuible, 012-C10) y el motivo cuando el
    fichero no compila (012-C11, sin defectos: nadie reescribe un fallo del generador)."""

    passed: bool
    defects: tuple[Defect, ...]
    unattributable: bool
    internal_error: str | None = None

    @property
    def score(self) -> float:
        return 1.0 if self.passed else 0.0


def lean_stage_result(result: ChronologyResult, bible: StoryBible) -> LeanStageResult:
    if result.result == "error":
        return LeanStageResult(
            passed=False, defects=(), unattributable=False, internal_error=result.reason
        )
    defects = lean_defects_from(result, bible)
    unattributable = any(defect.chapter is None for defect in defects)
    return LeanStageResult(
        passed=result.result == "passed", defects=defects, unattributable=unattributable
    )


def _banned_message(match: BannedTermMatch) -> str:
    where = "" if match.location == "chapter" else f", en {_PLACES[match.location]}"
    return f"«{match.variant}» está prohibido: {match.term} (nivel {match.level}{where})"


_PLACES = {"cover": "la portada", "sheet": "la ficha"}


def _match_detail(match: BannedTermMatch) -> dict[str, str]:
    """La coincidencia en el detalle de la decisión; el capítulo, solo si lo hay (012-C5, C6)."""
    detail = {
        "term": match.term,
        "level": match.level,
        "variant": match.variant,
        "location": match.location,
    }
    if match.chapter is not None:
        detail["chapter"] = str(match.chapter)
    return detail

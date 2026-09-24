"""Costura de las ventanas del writer y del editor (`architecture.md` §6.1 y §6.2).

`CandidateWindows` ensambla cada ventana desde la candidata (el outline que aplica 010) y el
recuperador de 016 (011-C07, 011-C08); el orquestador la recibe por el protocolo
`WindowBuilder`. El mensaje de la sesión es la ventana más las entradas de la llamada; lo que
lleva es lo que reserva el techo (011-C09)."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from story_maker.retrieval.queries import prospective_query, retrospective_query
from story_maker.store.models import (
    Brief,
    Chapter,
    Character,
    Fact,
    OutlineChapter,
    Place,
    StyleSheet,
    Version,
)
from story_maker.validators.chapter_rubric import (
    BLOCKING_CRITERIA,
    CHAPTER_CRITERIA,
    CRITERION_MEANING,
)

_TOKEN = re.compile(r"\S+")


@dataclass(frozen=True)
class WriterWindow:
    residents: Mapping[str, Any]
    retrieved: tuple[str, ...]
    target_words: int


@dataclass(frozen=True)
class EditorWindow:
    residents: Mapping[str, Any]
    retrieved: tuple[str, ...]


class WindowBuilder(Protocol):
    """Ensambla las ventanas desde la candidata; ningún rol pide contexto (§6.1)."""

    def writer(self, session: Session, version_id: int, chapter: int) -> WriterWindow: ...

    def editor(
        self, session: Session, version_id: int, chapter: int, title: str, text: str
    ) -> EditorWindow: ...


def _dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)


def writer_message(window: WriterWindow, defects: Sequence[Mapping[str, Any]]) -> str:
    """La ventana del writer y sus entradas: el objetivo de palabras y, al reescribir, los
    defectos del intento anterior; nunca su texto (011-C17)."""
    call_inputs: dict[str, Any] = {"target_words": window.target_words}
    if defects:
        call_inputs["defects"] = [dict(d) for d in defects]
    return _dump(
        {
            "window": {"residents": dict(window.residents), "retrieved": list(window.retrieved)},
            "call_inputs": call_inputs,
        }
    )


GATE_DEFECTS_NOTE = (
    "Defectos del gate de publicación sobre este capítulo. Un defecto de cronologia-lean "
    "prevalece sobre cumple-beats si el beat planificado era el origen de la incoherencia."
)


def editor_message(
    window: EditorWindow,
    title: str,
    text: str,
    lint_defects: Sequence[Mapping[str, Any]],
    gate_defects: Sequence[Mapping[str, Any]] = (),
) -> str:
    """La ventana del editor y sus entradas: el título y el texto entregados y los defectos de los
    linters (vacíos hasta 018). Nada de la sesión del writer (011-I8). En la reescritura dirigida,
    también los defectos Lean del gate, con su precedencia (012-C9, §9.4)."""
    call_inputs: dict[str, Any] = {
        "title": title,
        "text": text,
        "lint_defects": [dict(d) for d in lint_defects],
    }
    if gate_defects:
        call_inputs["gate_defects"] = {
            "note": GATE_DEFECTS_NOTE,
            "defects": [dict(d) for d in gate_defects],
        }
    return _dump(
        {
            "window": {"residents": dict(window.residents), "retrieved": list(window.retrieved)},
            "call_inputs": call_inputs,
        }
    )


class Retriever(Protocol):
    """El recuperador de 016 para la candidata y el capítulo: el texto de sus `top_k` tarjetas."""

    def __call__(
        self, session: Session, version_id: int, chapter: int, fragments: Sequence[str], top_k: int
    ) -> list[str]: ...


TARGET_WORDS = {"short": 1100, "medium": 1250, "long": 1400}
LITERAL_ENDING_WORDS = 300


def literal_ending(text: str) -> str:
    """Las últimas 300 palabras (como las cuenta `longitud-capitulo`), con su puntuación y sus
    saltos de párrafo, desde el principio de la primera (011-C07)."""
    starts = [m.start() for m in _TOKEN.finditer(text) if any(c.isalnum() for c in m.group())]
    return text[starts[-LITERAL_ENDING_WORDS] if len(starts) > LITERAL_ENDING_WORDS else 0 :]


def _fact(fact: Fact) -> dict[str, Any]:
    return {
        "id": fact.id,
        "subject_type": fact.subject_type,
        "character_id": fact.character_id,
        "place_id": fact.place_id,
        "attribute": fact.attribute,
        "value": fact.value,
    }


class CandidateWindows:
    """Ensambla las ventanas desde la candidata y el recuperador de 016 (011-C07, C08)."""

    def __init__(self, *, retriever: Retriever, top_k: Mapping[str, int]) -> None:
        self._retriever = retriever
        self._top_k = top_k

    def writer(self, session: Session, version_id: int, chapter: int) -> WriterWindow:
        """StyleSheet, proyección del outline (del resto de capítulos, solo los temas de sus
        revelaciones), resúmenes y final literal de los anteriores, obligatorios asignados, y
        los hechos y personajes de los beats; recupera con la consulta prospectiva."""
        outline = _outline(session, version_id)
        current = outline[chapter - 1]
        previous = _accepted(session, version_id, chapter)
        canon = _beat_canon(session, version_id, current)
        residents = {
            "style_sheet": _style_sheet(session, version_id),
            "outline": {
                "titles": [o.title for o in outline],
                "chapter": _chapter(current),
                "future_revelations": [
                    {"chapter": o.number, "theme": beat["revelation"]["theme"]}
                    for o in outline[chapter:]
                    for beat in _beats(o)
                    if beat.get("revelation")
                ],
            },
            "summaries": _summaries(previous),
            "literal_ending": literal_ending(previous[-1].text) if previous else None,
            "mandatory_elements": canon["mandatory_elements"],
            "facts": canon["facts"],
            "characters": canon["characters"],
        }
        fragments = prospective_query(session, version_id, chapter)
        retrieved = self._retriever(session, version_id, chapter, fragments, self._top_k["writer"])
        return WriterWindow(
            residents=residents,
            retrieved=tuple(retrieved),
            target_words=_target_words(session, version_id),
        )

    def editor(
        self, session: Session, version_id: int, chapter: int, title: str, text: str
    ) -> EditorWindow:
        """StyleSheet, resúmenes anteriores, el capítulo del outline con sus hechos, personajes y
        lugares, los obligatorios asignados, el índice de entidades y la rúbrica; recupera con la
        consulta retrospectiva. Nada de la sesión del writer ni del final literal."""
        current = _outline(session, version_id)[chapter - 1]
        residents = {
            "style_sheet": _style_sheet(session, version_id),
            "summaries": _summaries(_accepted(session, version_id, chapter)),
            "chapter": _chapter(current),
            **_beat_canon(session, version_id, current),
            "entities": {
                "characters": [_entity(c) for c in _characters(session, version_id)],
                "places": [_entity(p) for p in _places(session, version_id)],
            },
            "rubric": [
                {
                    "criterion": criterion,
                    "judges": CRITERION_MEANING[criterion],
                    "blocking": criterion in BLOCKING_CRITERIA,
                }
                for criterion in CHAPTER_CRITERIA
            ],
        }
        fragments = retrospective_query(text)
        retrieved = self._retriever(session, version_id, chapter, fragments, self._top_k["editor"])
        return EditorWindow(residents=residents, retrieved=tuple(retrieved))


def _beats(chapter: OutlineChapter) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], chapter.beats)


def _chapter(chapter: OutlineChapter) -> dict[str, Any]:
    return {"number": chapter.number, "title": chapter.title, "beats": _beats(chapter)}


def _summaries(previous: Sequence[Chapter]) -> list[dict[str, Any]]:
    return [{"chapter": c.number, "summary": c.summary} for c in previous]


def _entity(entity: Character | Place) -> dict[str, Any]:
    return {"id": entity.id, "name": entity.canonical_name}


def _characters(session: Session, version_id: int) -> list[Character]:
    query = select(Character).where(Character.version_id == version_id)
    return list(session.scalars(query.order_by(Character.id)))


def _places(session: Session, version_id: int) -> list[Place]:
    query = select(Place).where(Place.version_id == version_id)
    return list(session.scalars(query.order_by(Place.id)))


def _beat_canon(session: Session, version_id: int, chapter: OutlineChapter) -> dict[str, Any]:
    """Los personajes, los lugares y los hechos (con sus valores vigentes) que citan los beats
    del capítulo, y los hechos de los elementos obligatorios que tiene asignados."""
    beats = _beats(chapter)
    names = {name for beat in beats for name in beat.get("characters", [])}
    place_names = {e["place"] for beat in beats for e in beat.get("events", [])}
    used = {str(ref) for beat in beats for ref in beat.get("facts_used", [])}
    characters = [c for c in _characters(session, version_id) if c.canonical_name in names]
    places = [p for p in _places(session, version_id) if p.canonical_name in place_names]
    character_ids = {c.id for c in characters}
    place_ids = {p.id for p in places}
    facts = list(
        session.scalars(select(Fact).where(Fact.version_id == version_id).order_by(Fact.id))
    )
    cited = [
        f
        for f in facts
        if f.character_id in character_ids or f.place_id in place_ids or str(f.id) in used
    ]
    return {
        "mandatory_elements": _mandatory(facts, chapter),
        "facts": [_fact(f) for f in cited],
        "characters": [_entity(c) for c in characters],
        "places": [_entity(p) for p in places],
    }


def _outline(session: Session, version_id: int) -> list[OutlineChapter]:
    query = select(OutlineChapter).where(OutlineChapter.version_id == version_id)
    return list(session.scalars(query.order_by(OutlineChapter.number)))


def _accepted(session: Session, version_id: int, before: int) -> list[Chapter]:
    query = select(Chapter).where(Chapter.version_id == version_id, Chapter.number < before)
    return list(session.scalars(query.order_by(Chapter.number)))


def _style_sheet(session: Session, version_id: int) -> Any:
    query = select(StyleSheet.content).where(StyleSheet.version_id == version_id)
    return session.scalars(query).one()


def _mandatory(facts: Sequence[Fact], chapter: OutlineChapter) -> list[dict[str, Any]]:
    """Los hechos de los elementos personales asignados al capítulo."""
    assigned = {str(e) for e in cast(list[Any], chapter.assigned_elements)}
    return [
        _fact(f)
        for f in facts
        if f.personal_element_id is not None and str(f.personal_element_id) in assigned
    ]


def _target_words(session: Session, version_id: int) -> int:
    """El objetivo de la `Extension` del brief; media si el brief no la trae."""
    version = session.get_one(Version, version_id)
    query = select(Brief.content).where(Brief.novel_id == version.novel_id)
    content = session.scalars(query).one_or_none() or {}
    length = content.get("length") if isinstance(content, dict) else None
    return TARGET_WORDS.get(str(length), TARGET_WORDS["medium"])

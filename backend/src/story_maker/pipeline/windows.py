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

from story_maker.retrieval.queries import prospective_query
from story_maker.store.models import (
    Brief,
    Chapter,
    Character,
    Fact,
    OutlineChapter,
    StyleSheet,
    Version,
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


def editor_message(
    window: EditorWindow, title: str, text: str, lint_defects: Sequence[Mapping[str, Any]]
) -> str:
    """La ventana del editor y sus entradas: el título y el texto entregados y los defectos de los
    linters (vacíos hasta 018). Nada de la sesión del writer (011-I8)."""
    return _dump(
        {
            "window": {"residents": dict(window.residents), "retrieved": list(window.retrieved)},
            "call_inputs": {
                "title": title,
                "text": text,
                "lint_defects": [dict(d) for d in lint_defects],
            },
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
        outline = _outline(session, version_id)
        current = outline[chapter - 1]
        beats = cast(list[dict[str, Any]], current.beats)
        previous = _accepted(session, version_id, chapter)
        names = {name for beat in beats for name in beat.get("characters", [])}
        characters = [
            c
            for c in session.scalars(
                select(Character).where(Character.version_id == version_id).order_by(Character.id)
            )
            if c.canonical_name in names
        ]
        character_ids = {c.id for c in characters}
        used = {str(ref) for beat in beats for ref in beat.get("facts_used", [])}
        facts = list(
            session.scalars(select(Fact).where(Fact.version_id == version_id).order_by(Fact.id))
        )
        residents = {
            "style_sheet": _style_sheet(session, version_id),
            "outline": {
                "titles": [o.title for o in outline],
                "chapter": {"number": current.number, "title": current.title, "beats": beats},
                "future_revelations": [
                    {"chapter": o.number, "theme": beat["revelation"]["theme"]}
                    for o in outline[chapter:]
                    for beat in cast(list[dict[str, Any]], o.beats)
                    if beat.get("revelation")
                ],
            },
            "summaries": [{"chapter": c.number, "summary": c.summary} for c in previous],
            "literal_ending": literal_ending(previous[-1].text) if previous else None,
            "mandatory_elements": _mandatory(facts, current),
            "facts": [
                _fact(f) for f in facts if f.character_id in character_ids or str(f.id) in used
            ],
            "characters": [{"id": c.id, "name": c.canonical_name} for c in characters],
        }
        fragments = prospective_query(session, version_id, chapter)
        retrieved = self._retriever(session, version_id, chapter, fragments, self._top_k["writer"])
        return WriterWindow(
            residents=residents,
            retrieved=tuple(retrieved),
            target_words=_target_words(session, version_id),
        )


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

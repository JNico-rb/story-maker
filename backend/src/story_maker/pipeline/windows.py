"""Costura de las ventanas del writer y del editor (`architecture.md` §6.1 y §6.2).

Qué residentes y qué recuperados lleva cada ventana (011-C07, 011-C08) depende del outline que
aplica 010 y del recuperador de 016; hasta que estén, el orquestador recibe quien ensambla las
ventanas por este protocolo. Aquí solo se compone el mensaje de la sesión: la ventana más las
entradas de la llamada. Lo que el mensaje lleva es lo que reserva el techo (011-C09)."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy.orm import Session


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

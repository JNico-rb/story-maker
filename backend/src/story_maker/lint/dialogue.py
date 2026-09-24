"""Diálogo y narración de un párrafo (`Reglas comunes`, spec 018): raya de diálogo, comillas
e intervenciones, para `linter-consistencia`."""

from __future__ import annotations

_QUOTE_PAIRS = (("«", "»"), ("“", "”"), ('"', '"'))
_DASH = "—"


def _quoted_spans(line: str) -> list[tuple[int, int]]:
    """Los tramos entre comillas de `line`, como (inicio, fin) exclusivo."""
    spans = []
    index = 0
    length = len(line)
    while index < length:
        matched = False
        for open_mark, close_mark in _QUOTE_PAIRS:
            if line[index] == open_mark:
                end = line.find(close_mark, index + 1)
                if end != -1:
                    spans.append((index, end + 1))
                    index = end + 1
                    matched = True
                    break
        if not matched:
            index += 1
    return spans


def narration_text(paragraph: str) -> str:
    """El texto de narración de `paragraph`: fuera de raya de diálogo y de comillas."""
    parts = []
    for line in paragraph.split("\n"):
        if line.lstrip().startswith(_DASH):
            segments = line.split(_DASH)
            if segments[0].strip():
                parts.append(segments[0])
            parts.extend(segments[2::2])
        else:
            position = 0
            for start, end in _quoted_spans(line):
                if start > position:
                    parts.append(line[position:start])
                position = end
            if position < len(line):
                parts.append(line[position:])
    return "\n".join(parts)


def interventions(paragraph: str) -> list[str]:
    """Las intervenciones de `paragraph`: el diálogo de una línea con raya (una por línea,
    juntando sus tramos), o cada texto entre comillas."""
    result = []
    for line in paragraph.split("\n"):
        if line.lstrip().startswith(_DASH):
            segments = line.split(_DASH)
            dialogue_parts = segments[1::2]
            if dialogue_parts:
                result.append(" ".join(dialogue_parts))
        else:
            for start, end in _quoted_spans(line):
                result.append(line[start:end])
    return result

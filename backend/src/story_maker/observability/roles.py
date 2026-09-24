"""Etiqueta de Langfuse de cada rol: nombre de su traza, su span y su `PromptVersionado`.

`definitions.md` §12.2: columna «Etiqueta»."""

from __future__ import annotations

ROLE_LABELS: dict[str, str] = {
    "interviewer": "entrevistador",
    "extractor": "extractor",
    "planner": "planner",
    "writer": "writer",
    "editor": "editor",
    "judge": "juez",
    "visual_reviewer": "revisor-visual",
}

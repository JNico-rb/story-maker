"""Interpretación de la salida de la compilación Lean (tabla de 007-C13)."""

from __future__ import annotations

from typing import Any

from story_maker.formal.lean_output import interpret


def test_the_compilation_output_gives_the_result_of_its_row(lean_row: Any) -> None:
    lean_row.check(interpret(lean_row.output))

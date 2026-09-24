"""Datos compartidos de la spec 007: la cronología de fixture («Datos de los casos») y la tabla
de salidas de la compilación de 007-C13, que 007-C15 repite por el modo github."""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from typing import Any

import pytest

from story_maker.formal.chronology import (
    Chronology,
    ChronologyCharacter,
    ChronologyEvent,
    Presence,
)
from story_maker.formal.lean_output import LeanOutput
from story_maker.formal.result import INVARIANTS, ChronologyResult, Invariant

RECIPIENT, GRANDMOTHER, DOG = 11, 12, 13
PLACE_A, PLACE_B = 21, 22


def fixture_chronology() -> Chronology:
    """El destinatario (11), la abuela (12), el perro (13); lugares 21 y 22; eventos 31, 32 (brief),
    41, 42 (registrados) y 51 (planificado)."""
    return Chronology(
        events=(
            ChronologyEvent(
                id=31,
                moment=dt.datetime(1998, 5, 14, 12, 0),
                place_id=PLACE_A,
                presences=(Presence(RECIPIENT, 8), Presence(GRANDMOTHER)),
                type="ordinary",
                excluded_character_id=None,
                analepsis=False,
                origin="brief",
                chapter=None,
                beat=None,
            ),
            ChronologyEvent(
                id=32,
                moment=dt.datetime(2010, 9, 1, 12, 0),
                place_id=PLACE_B,
                presences=(Presence(RECIPIENT),),
                type="exclusion",
                excluded_character_id=GRANDMOTHER,
                analepsis=False,
                origin="brief",
                chapter=None,
                beat=None,
            ),
            ChronologyEvent(
                id=41,
                moment=dt.datetime(2026, 3, 2, 10, 0),
                place_id=PLACE_A,
                presences=(Presence(RECIPIENT), Presence(DOG)),
                type="ordinary",
                excluded_character_id=None,
                analepsis=False,
                origin="recorded",
                chapter=1,
                beat=1,
            ),
            ChronologyEvent(
                id=42,
                moment=dt.datetime(2005, 7, 1, 18, 0),
                place_id=PLACE_B,
                presences=(Presence(RECIPIENT), Presence(GRANDMOTHER)),
                type="ordinary",
                excluded_character_id=None,
                analepsis=True,
                origin="recorded",
                chapter=2,
                beat=1,
            ),
            ChronologyEvent(
                id=51,
                moment=dt.datetime(2026, 5, 10, 9, 0),
                place_id=PLACE_A,
                presences=(Presence(RECIPIENT),),
                type="ordinary",
                excluded_character_id=None,
                analepsis=False,
                origin="planned",
                chapter=3,
                beat=2,
            ),
        ),
        characters=(
            ChronologyCharacter(RECIPIENT, dt.date(1990, 5, 14)),
            ChronologyCharacter(GRANDMOTHER, dt.date(1936, 2, 29)),
            ChronologyCharacter(DOG, None),
        ),
        novum_date=dt.date(2024, 11, 1),
    )


@pytest.fixture
def chronology() -> Chronology:
    return fixture_chronology()


# --- Tabla de 007-C13: salida de la compilación → resultado -----------------------------------

ADMITTED = ["propext", "Classical.choice", "Quot.sound"]


def report(**violated: list[int]) -> dict[str, Any]:
    """JSON del informe: cumplen todos salvo los violados, con su testigo."""
    return {
        t: {"cumple": False, "testigo": violated[t]} if t in violated else {"cumple": True}
        for t in INVARIANTS
    }


def audits(**overrides: list[str]) -> dict[str, list[str]]:
    """Axiomas de cada teorema `cumpleTn`: admitidos salvo los que se indiquen."""
    return {f"cumple{t}": overrides.get(t, ["propext"]) for t in INVARIANTS}


def lean_text(
    json_report: dict[str, Any] | None,
    axioms: dict[str, list[str]],
    errors: tuple[str, ...] = (),
    prefix: str = "",
) -> str:
    """Salida con la forma de `lean`: diagnósticos, la línea del informe y `#print axioms`."""
    lines = [f"Cronologia.lean:{30 + i}:0: error: {e}" for i, e in enumerate(errors)]
    if json_report is not None:
        lines.append(f"{prefix}CRONOLOGIA-LEAN {json.dumps(json_report, separators=(',', ':'))}")
    for name, used in axioms.items():
        if used:
            lines.append(f"{prefix}'{name}' depends on axioms: [{', '.join(used)}]")
        else:
            lines.append(f"{prefix}'{name}' does not depend on any axioms")
    return "\n".join(lines) + "\n"


ALL_HOLD: dict[Invariant, bool] = dict.fromkeys(INVARIANTS, True)


@dataclass(frozen=True)
class LeanRow:
    name: str
    output: LeanOutput
    expected: str
    holds: dict[Invariant, bool] = field(default_factory=dict)
    witnesses: dict[Invariant, tuple[int, ...]] = field(default_factory=dict)
    reason_contains: tuple[str, ...] = ()

    def check(self, result: ChronologyResult) -> None:
        assert result.result == self.expected, result
        assert dict(result.holds) == self.holds
        assert dict(result.witnesses) == self.witnesses
        for fragment in self.reason_contains:
            assert result.reason is not None
            assert fragment in result.reason, result.reason


LEAN_ROWS = (
    LeanRow(
        "compila-cumple-todo",
        LeanOutput(0, lean_text(report(), audits(T2=ADMITTED, T5=[]))),
        "passed",
        holds=ALL_HOLD,
    ),
    LeanRow(
        "compila-cumple-todo-con-prefijo",
        LeanOutput(0, lean_text(report(), audits(), prefix="Cronologia.lean:12:0: info: ")),
        "passed",
        holds=ALL_HOLD,
    ),
    LeanRow(
        "no-compila-T4",
        LeanOutput(
            1,
            lean_text(
                report(T4=[12, 32, 71]),
                audits(T4=["propext", "sorryAx"]),
                errors=("decide failed: proposition compruebaT4 cronologia = true is false",),
            ),
        ),
        "failed",
        holds={**ALL_HOLD, "T4": False},
        witnesses={"T4": (12, 32, 71)},
    ),
    LeanRow(
        "no-compila-cumple-todo",
        LeanOutput(1, lean_text(report(), audits(), errors=("unknown identifier 'x'",))),
        "error",
        reason_contains=("unknown identifier 'x'",),
    ),
    LeanRow(
        "no-compila-sin-json",
        LeanOutput(1, lean_text(None, {}, errors=("unexpected token 'eventos'",))),
        "error",
        reason_contains=("unexpected token 'eventos'",),
    ),
    LeanRow(
        "compila-con-invariante-violado",
        LeanOutput(0, lean_text(report(T2=[11, 31, 9, 8]), audits())),
        "error",
        reason_contains=("incoherentes",),
    ),
    LeanRow(
        "auditoria-sorry",
        LeanOutput(0, lean_text(report(), audits(T3=["propext", "sorryAx"]))),
        "error",
        reason_contains=("cumpleT3", "sorryAx"),
    ),
    LeanRow(
        "auditoria-axioma-propio",
        LeanOutput(0, lean_text(report(), audits(T1=["trampa"]))),
        "error",
        reason_contains=("cumpleT1", "trampa"),
    ),
)


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "lean_row" in metafunc.fixturenames:
        metafunc.parametrize("lean_row", LEAN_ROWS, ids=[row.name for row in LEAN_ROWS])

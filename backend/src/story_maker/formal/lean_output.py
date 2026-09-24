"""Interpretación de la salida de la compilación Lean, la misma en los dos modos (007-I9).

La salida es la de `lean` sobre un `FicheroDeCronologia`: sus diagnósticos, la línea del informe
(`CRONOLOGIA-LEAN {json}`) y los `#print axioms` de los cinco teoremas `cumpleT1` a `cumpleT5`.
Solo es `passed` lo que compila, pasa la auditoría y cumple los cinco invariantes (007-I2).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from story_maker.formal.result import INVARIANTS, ChronologyResult, Invariant

REPORT_MARKER = "CRONOLOGIA-LEAN "
# Los tres axiomas estándar de Lean; ni `sorryAx`, ni axiomas propios, ni `Lean.ofReduceBool`
# (confiar en el compilador para evaluar), 007-I11.
ADMITTED_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})
THEOREMS: dict[Invariant, str] = {t: f"cumple{t}" for t in INVARIANTS}

_DEPENDS_RE = re.compile(r"'(?P<name>[^']+)' depends on axioms: \[(?P<axioms>[^\]]*)\]")
_NO_AXIOMS_RE = re.compile(r"'(?P<name>[^']+)' does not depend on any axioms")


@dataclass(frozen=True)
class LeanOutput:
    """Salida de compilar un `FicheroDeCronologia`: código de salida y texto (stdout y stderr)."""

    exit_code: int
    output: str


@dataclass(frozen=True)
class Report:
    holds: dict[Invariant, bool]
    witnesses: dict[Invariant, tuple[int, ...]]


def _is_witness(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(n, int) and not isinstance(n, bool) for n in value)
    )


def _report_from(data: Any) -> Report | None:
    if not isinstance(data, dict) or set(data) != set(INVARIANTS):
        return None
    holds: dict[Invariant, bool] = {}
    witnesses: dict[Invariant, tuple[int, ...]] = {}
    for t in INVARIANTS:
        entry = data[t]
        if not isinstance(entry, dict) or not isinstance(entry.get("cumple"), bool):
            return None
        holds[t] = entry["cumple"]
        if not holds[t]:
            if not _is_witness(entry.get("testigo")):
                return None
            witnesses[t] = tuple(entry["testigo"])
    return Report(holds, witnesses)


def parse_report(output: str) -> Report | None:
    """El informe JSON del fichero, o nada si falta o no tiene la forma del informe."""
    for line in output.splitlines():
        _, marker, payload = line.partition(REPORT_MARKER)
        if marker:
            try:
                return _report_from(json.loads(payload))
            except json.JSONDecodeError:
                return None
    return None


def parse_audit(output: str) -> dict[str, frozenset[str]]:
    """Axiomas de cada teorema auditado con `#print axioms`."""
    audit: dict[str, frozenset[str]] = {}
    for line in output.splitlines():
        if match := _DEPENDS_RE.search(line):
            names = (a.strip() for a in match["axioms"].split(","))
            audit[match["name"]] = frozenset(a for a in names if a)
        elif match := _NO_AXIOMS_RE.search(line):
            audit[match["name"]] = frozenset()
    return audit


def audit_problems(audit: dict[str, frozenset[str]], theorems: list[str]) -> list[str]:
    problems = []
    for name in theorems:
        if name not in audit:
            problems.append(f"{name}: sin auditoría de axiomas")
        for axiom in sorted(audit.get(name, frozenset()) - ADMITTED_AXIOMS):
            problems.append(f"{name} depende del axioma no admitido {axiom}")
    return problems


def first_diagnostic(output: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    errors = [line for line in lines if "error:" in line]
    others = [line for line in lines if REPORT_MARKER not in line]
    return (errors or others or ["la compilación no dio ningún diagnóstico"])[0]


def interpret(lean: LeanOutput) -> ChronologyResult:
    """Resultado del fichero según la tabla de 007-C13."""
    report = parse_report(lean.output)
    compiled = lean.exit_code == 0
    if report is None:
        return ChronologyResult("error", reason=f"sin informe: {first_diagnostic(lean.output)}")
    violated = [t for t in INVARIANTS if not report.holds[t]]
    held = [THEOREMS[t] for t in INVARIANTS if report.holds[t]]
    problems = audit_problems(parse_audit(lean.output), held)
    if compiled and violated:
        return ChronologyResult(
            "error",
            reason=f"compila, pero el informe da {', '.join(violated)} sin cumplir: "
            "son incoherentes",
        )
    if compiled and not problems:
        return ChronologyResult("passed", holds=report.holds)
    if compiled:
        return ChronologyResult("error", reason="; ".join(problems))
    if not violated or problems:
        return ChronologyResult(
            "error", reason="; ".join([first_diagnostic(lean.output), *problems])
        )
    return ChronologyResult("failed", holds=report.holds, witnesses=report.witnesses)

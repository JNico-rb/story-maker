"""Interpretación de la salida de la compilación Lean (tabla de 007-C13 y 007-I2)."""

from __future__ import annotations

from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from story_maker.formal.lean_output import LeanOutput, interpret
from story_maker.formal.result import INVARIANTS


def test_the_compilation_output_gives_the_result_of_its_row(lean_row: Any) -> None:
    lean_row.check(interpret(lean_row.output))


# --- 007-I2 ----------------------------------------------------------------------------------

AXIOMS = ["propext", "Classical.choice", "Quot.sound", "sorryAx", "trampa", "Lean.ofReduceBool"]
ADMITTED = {"propext", "Classical.choice", "Quot.sound"}


@st.composite
def compilations(draw: st.DrawFn) -> dict[str, Any]:
    """Cualquier combinación de estado de la compilación, informe y auditoría."""
    holds = {t: draw(st.booleans()) for t in INVARIANTS}
    witnesses = {
        t: draw(st.lists(st.integers(1, 99), min_size=2, max_size=4))
        for t in INVARIANTS
        if not holds[t]
    }
    audit = {
        f"cumple{t}": draw(st.lists(st.sampled_from(AXIOMS), unique=True, max_size=3))
        for t in INVARIANTS
        if draw(st.integers(0, 9)) > 0  # a veces falta la auditoría de un teorema
    }
    return {
        "exit_code": draw(st.sampled_from([0, 1])),
        "report": draw(st.booleans()),
        "holds": holds,
        "witnesses": witnesses,
        "audit": audit,
    }


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=300)
@given(case=compilations())
def test_only_what_compiles_passes_the_audit_and_meets_all_five_is_passed(
    lean_texts: Any, case: dict[str, Any]
) -> None:
    json_report = lean_texts.report(**case["witnesses"]) if case["report"] else None
    output = LeanOutput(case["exit_code"], lean_texts.text(json_report, case["audit"]))

    result = interpret(output)

    clean_audit = all(
        f"cumple{t}" in case["audit"] and set(case["audit"][f"cumple{t}"]) <= ADMITTED
        for t in INVARIANTS
    )
    should_pass = (
        case["exit_code"] == 0 and case["report"] and all(case["holds"].values()) and clean_audit
    )
    assert (result.result == "passed") == should_pass
    assert result.result in ("passed", "failed", "error")
    if result.result == "passed":
        assert dict(result.holds) == dict.fromkeys(INVARIANTS, True)
        assert dict(result.witnesses) == {}
    if result.result == "failed":
        assert case["exit_code"] != 0
        violated = {t for t, h in case["holds"].items() if not h}
        assert violated
        assert set(result.witnesses) == violated
    if result.result == "error":
        assert dict(result.holds) == {}
        assert result.reason

"""Verificación de la candidata de una ejecución, con el doble del `VerificadorFormal` (007-C09 a
007-C12, 007-I7, 007-I12)."""

from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path
from typing import Any

import pytest

from story_maker.formal.candidate import verify_candidate
from story_maker.formal.double import ProgrammedFormalVerifier
from story_maker.formal.result import ChronologyResult, VerificationOutcome, VerifierInterruption

NOW = dt.datetime(2026, 9, 24, 12, 0)
ALL_HOLD = dict.fromkeys(("T1", "T2", "T3", "T4", "T5"), True)


def candidate_rows(rows: Any) -> list[Any]:
    """La candidata de 007-C07: Rosa (12) se va en 32 y vuelve en 71; 44 (cap. 5) es anterior a
    43 (cap. 3)."""
    return [
        rows.character(11, "Marta", dt.date(1990, 5, 14)),
        rows.character(12, "Rosa", dt.date(1936, 2, 29)),
        rows.place(21, "la feria del pueblo"),
        rows.place(22, "la estación"),
        rows.place(23, "el faro"),
        rows.event(32, dt.datetime(2010, 9, 1, 12, 0), 22, excluded=12),
        rows.event(43, dt.datetime(2026, 5, 2, 18, 30), 21, origin="recorded", chapter=3, beat=1),
        rows.event(44, dt.datetime(2026, 5, 1, 9, 0), 23, origin="recorded", chapter=5, beat=4),
        rows.event(71, dt.datetime(2026, 8, 15, 12, 0), 23, origin="recorded", chapter=7, beat=2),
        rows.presence(32, 11),
        rows.presence(43, 11),
        rows.presence(44, 11),
        rows.presence(71, 12),
    ]


@pytest.fixture
def lab(store: Any, rows: Any, tmp_path: Path) -> dict[str, Any]:
    novel = store.novel()
    candidate = store.candidate(novel, candidate_rows(rows))
    return {"run": store.run(novel, candidate), "data": tmp_path / "data"}


async def verify(store: Any, lab: dict[str, Any], *outcomes: VerificationOutcome) -> Any:
    double = ProgrammedFormalVerifier(outcomes)
    verification = await verify_candidate(
        store.session_factory, double, run_id=lab["run"], data_dir=lab["data"], now=NOW
    )
    return verification, double


def outside_files(root: Path) -> set[str]:
    """Lo que hay en `root` fuera del directorio de datos y de la base de la prueba."""
    return {
        str(p.relative_to(root))
        for p in root.rglob("*")
        if not p.is_relative_to(root / "data") and not p.name.startswith("story-maker.db")
    }


# --- 007-C09, 007-I7, 007-I12 ----------------------------------------------------------------


async def test_a_verification_that_passes_leaves_its_file_and_its_row(
    store: Any, lab: dict[str, Any], tmp_path: Path
) -> None:
    before = outside_files(tmp_path)

    verification, double = await verify(store, lab, ChronologyResult("passed", holds=ALL_HOLD))

    saved = verification.file_path
    assert saved is not None
    assert saved.resolve().is_relative_to(lab["data"].resolve())
    assert saved.read_text(encoding="utf-8") == double.received[0]
    assert outside_files(tmp_path) == before
    rows = store.chronology_files()
    assert len(rows) == 1
    row = rows[0]
    assert row.run_id == lab["run"]
    assert row.content_hash == hashlib.sha256(saved.read_bytes()).hexdigest()
    assert row.content_hash == verification.content_hash
    assert row.result == "passed"
    assert not (row.detail or {}).get("witnesses")
    assert verification.outcome == ChronologyResult("passed", holds=ALL_HOLD)
    assert verification.defects == ()


# --- 007-C10 ---------------------------------------------------------------------------------


async def test_a_violated_invariant_leaves_the_row_failed_and_returns_the_defects(
    store: Any, lab: dict[str, Any]
) -> None:
    failed = ChronologyResult(
        "failed",
        holds={**ALL_HOLD, "T1": False, "T4": False},
        witnesses={"T1": (43, 44), "T4": (12, 32, 71)},
    )

    verification, _ = await verify(store, lab, failed)

    (row,) = store.chronology_files()
    assert row.result == "failed"
    assert row.detail["witnesses"] == {"T1": [43, 44], "T4": [12, 32, 71]}
    assert verification.outcome == failed
    assert [(d.chapter, d.message[:2]) for d in verification.defects] == [
        (3, "T1"),
        (5, "T1"),
        (7, "T4"),
    ]
    assert all(d.validator == "cronologia-lean" and d.blocking for d in verification.defects)
    assert "Rosa" in verification.defects[2].message


# --- 007-C11 ---------------------------------------------------------------------------------


async def test_a_file_that_does_not_compile_for_another_reason_is_an_error_never_passed(
    store: Any, lab: dict[str, Any]
) -> None:
    error = ChronologyResult("error", reason="unexpected token 'eventos'")

    verification, _ = await verify(store, lab, error)

    (row,) = store.chronology_files()
    assert row.result == "error"
    assert row.detail == {"reason": "unexpected token 'eventos'"}
    assert verification.outcome.result == "error"
    assert dict(verification.outcome.holds) == {}
    assert verification.defects == ()


# --- 007-C12 ---------------------------------------------------------------------------------


@pytest.mark.parametrize("reason", ["verifier_unreachable", "verifier_timeout"])
async def test_without_a_verdict_there_is_no_row(
    store: Any, lab: dict[str, Any], reason: Any
) -> None:
    verification, _ = await verify(store, lab, VerifierInterruption(reason))

    assert verification.outcome == VerifierInterruption(reason)
    assert verification.defects == ()
    assert store.chronology_files() == []

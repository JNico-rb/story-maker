"""Órdenes de la verificación Lean fuera del servidor (007-C20 a 007-C24 en la CI; el workflow del
modo github, 007-I9 y 007-I10). Aquí, con el sustituto de `lake`: Lean solo corre en la CI."""

from __future__ import annotations

import base64
import gzip
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from story_maker.formal.github import encode_input, read_result
from story_maker.formal.lean_ci import (
    InvalidInput,
    check_expectation,
    decode_input,
    main,
    run_ci_files,
)
from story_maker.formal.lean_output import LeanOutput, interpret

FAKE_LAKE = Path(__file__).with_name("fake_lake.py")
LIBRARY = [f"Chronology.compruebaT{n}_decide" for n in range(1, 6)]
SOURCE = "import Chronology\n\n-- ⟨fichero⟩ de prueba\n"


def passed(t: Any) -> LeanOutput:
    return LeanOutput(0, t.text(t.report(), t.audits()))


def failed(t: Any, **witnesses: list[int]) -> LeanOutput:
    sorry = {name: ["propext", "sorryAx"] for name in witnesses}
    return LeanOutput(1, t.text(t.report(**witnesses), t.audits(**sorry), errors=("falla",)))


# --- Expectativas de la CI -------------------------------------------------------------------


def test_a_file_expected_to_pass_passes_only_if_it_passes(lean_texts: Any) -> None:
    expectation = {"resultado": "passed"}

    assert check_expectation(expectation, passed(lean_texts)) is None
    assert check_expectation(expectation, failed(lean_texts, T4=[13, 61, 63])) is not None


def test_a_negative_file_passes_only_with_its_invariant_and_its_first_witness(
    lean_texts: Any,
) -> None:
    expectation = {"resultado": "failed", "testigos": {"T1": [61, 62]}}

    assert check_expectation(expectation, failed(lean_texts, T1=[61, 62])) is None
    other_witness = check_expectation(expectation, failed(lean_texts, T1=[61, 63]))
    assert other_witness is not None
    assert "61, 63" in other_witness
    assert check_expectation(expectation, failed(lean_texts, T1=[61, 62], T3=[11, 61, 62]))
    compiles = check_expectation(expectation, passed(lean_texts))
    assert compiles is not None
    assert "passed" in compiles


def test_a_control_file_passes_only_if_it_is_an_error_for_its_reason(lean_texts: Any) -> None:
    expectation = {"resultado": "error", "compila": False, "motivo": ["sorryAx"]}
    t = lean_texts
    with_sorry = LeanOutput(
        1,
        t.text(t.report(), t.audits(T1=["sorryAx"]), errors=("declaration uses 'sorry'",)),
    )
    compiled_with_axiom = LeanOutput(0, t.text(t.report(), t.audits(T1=["trampa"])))

    assert check_expectation(expectation, with_sorry) is None
    assert check_expectation(expectation, passed(t)) is not None
    assert check_expectation(expectation, compiled_with_axiom) is not None
    assert (
        check_expectation(
            {"resultado": "error", "compila": True, "motivo": ["trampa"]}, compiled_with_axiom
        )
        is None
    )


def test_the_library_audit_passes_only_with_admitted_axioms_for_every_theorem(
    lean_texts: Any,
) -> None:
    expectation = {"auditoria": LIBRARY}
    clean = {name: ["propext"] for name in LIBRARY}

    assert check_expectation(expectation, LeanOutput(0, lean_texts.text(None, clean))) is None
    tainted = {**clean, LIBRARY[2]: ["propext", "Lean.ofReduceBool"]}
    problem = check_expectation(expectation, LeanOutput(0, lean_texts.text(None, tainted)))
    assert problem is not None
    assert "Lean.ofReduceBool" in problem
    missing = {name: ["propext"] for name in LIBRARY[:-1]}
    assert check_expectation(expectation, LeanOutput(0, lean_texts.text(None, missing)))
    assert check_expectation(expectation, LeanOutput(1, lean_texts.text(None, clean)))


# --- El job formal de la CI ------------------------------------------------------------------


@pytest.fixture
def ci_lean_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    lean_dir = tmp_path / "lean"
    (lean_dir / "pruebas").mkdir(parents=True)
    monkeypatch.setenv("FAKE_LAKE_SCENARIO", str(tmp_path / "scenario.json"))
    monkeypatch.setenv("FAKE_LAKE_LOG", str(tmp_path / "log.jsonl"))
    return lean_dir


def program_ci(lean_dir: Path, files: dict[str, tuple[dict[str, Any], LeanOutput]]) -> None:
    (lean_dir / "pruebas" / "esperado.json").write_text(
        json.dumps({name: expectation for name, (expectation, _) in files.items()}),
        encoding="utf-8",
    )
    for name in files:
        (lean_dir / "pruebas" / name).write_text(SOURCE, encoding="utf-8")
    scenario = {
        "por_fichero": {
            name: {"exit_code": out.exit_code, "output": out.output}
            for name, (_, out) in files.items()
        }
    }
    (lean_dir.parent / "scenario.json").write_text(json.dumps(scenario), encoding="utf-8")


def test_the_ci_is_green_when_every_file_gives_what_is_expected(
    ci_lean_dir: Path, lean_texts: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    program_ci(
        ci_lean_dir,
        {
            "dorado.lean": ({"resultado": "passed"}, passed(lean_texts)),
            "negativo-T4.lean": (
                {"resultado": "failed", "testigos": {"T4": [13, 61, 63]}},
                failed(lean_texts, T4=[13, 61, 63]),
            ),
        },
    )

    assert run_ci_files(ci_lean_dir, lake=(sys.executable, str(FAKE_LAKE))) == 0
    assert capsys.readouterr().out.count("OK ") == 2


def test_the_ci_is_red_when_a_negative_file_compiles_or_gives_another_witness(
    ci_lean_dir: Path, lean_texts: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    program_ci(
        ci_lean_dir,
        {
            "dorado.lean": ({"resultado": "passed"}, passed(lean_texts)),
            "negativo-T1.lean": (
                {"resultado": "failed", "testigos": {"T1": [61, 62]}},
                passed(lean_texts),
            ),
            "negativo-T4.lean": (
                {"resultado": "failed", "testigos": {"T4": [13, 61, 63]}},
                failed(lean_texts, T4=[13, 61, 64]),
            ),
        },
    )

    assert run_ci_files(ci_lean_dir, lake=(sys.executable, str(FAKE_LAKE))) == 1
    out = capsys.readouterr().out
    assert "FALLO negativo-T1.lean" in out
    assert "FALLO negativo-T4.lean" in out
    assert "OK dorado.lean" in out


def test_the_ci_is_red_when_a_file_has_no_expectation(
    ci_lean_dir: Path, lean_texts: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    program_ci(ci_lean_dir, {"dorado.lean": ({"resultado": "passed"}, passed(lean_texts))})
    (ci_lean_dir / "pruebas" / "sin-expectativa.lean").write_text(SOURCE, encoding="utf-8")

    assert run_ci_files(ci_lean_dir, lake=(sys.executable, str(FAKE_LAKE))) == 1
    assert "FALLO sin-expectativa.lean" in capsys.readouterr().out


# --- El workflow del modo github -------------------------------------------------------------


def test_the_workflow_input_decodes_to_the_file() -> None:
    assert decode_input(encode_input(SOURCE)) == SOURCE


@pytest.mark.parametrize(
    "value",
    [
        "esto no es base64!",
        base64.b64encode(b"no es gzip").decode(),
        base64.b64encode(gzip.compress(b"\xff\xfe no es utf-8")).decode(),
        base64.b64encode(gzip.compress(b"x" * 3_000_000)).decode(),  # descomprime demasiado
        "",
    ],
    ids=["no-base64", "no-gzip", "no-utf8", "demasiado-grande", "vacio"],
)
def test_an_input_that_is_not_a_gzip_base64_file_is_rejected_before_decompressing(
    value: str,
) -> None:
    with pytest.raises(InvalidInput):
        decode_input(value)


def test_the_workflow_decodes_a_valid_input_into_the_file_to_compile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FICHERO", encode_input(SOURCE))
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "github_output"))

    code = main(
        ["decodificar", str(tmp_path / "Cronologia.lean"), str(tmp_path / "resultado.json")]
    )

    assert code == 0
    assert (tmp_path / "Cronologia.lean").read_text(encoding="utf-8") == SOURCE
    assert not (tmp_path / "resultado.json").exists()
    assert (tmp_path / "github_output").read_text(encoding="utf-8") == "valido=true\n"


def test_the_workflow_answers_an_invalid_input_with_an_error_result_and_compiles_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FICHERO", "esto no es base64!")
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "github_output"))

    code = main(
        ["decodificar", str(tmp_path / "Cronologia.lean"), str(tmp_path / "resultado.json")]
    )

    assert code == 0
    assert not (tmp_path / "Cronologia.lean").exists()
    assert (tmp_path / "github_output").read_text(encoding="utf-8") == "valido=false\n"
    result = interpret(read_result(zip_of(tmp_path / "resultado.json")))
    assert result.result == "error"
    assert result.reason is not None
    assert "input" in result.reason


def zip_of(path: Path) -> bytes:
    """El artefacto tal como lo sube `actions/upload-artifact`: un zip con `resultado.json`."""
    archive = shutil.make_archive(str(path.with_suffix("")), "zip", path.parent, path.name)
    return Path(archive).read_bytes()


def test_the_workflow_result_reads_back_as_the_local_mode_reads_the_same_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, lean_row: Any
) -> None:
    lean_dir = tmp_path / "lean"
    lean_dir.mkdir()
    (tmp_path / "Cronologia.lean").write_text(SOURCE, encoding="utf-8")
    scenario = {"lean": {"exit_code": lean_row.output.exit_code, "output": lean_row.output.output}}
    (tmp_path / "scenario.json").write_text(json.dumps(scenario), encoding="utf-8")
    monkeypatch.setenv("FAKE_LAKE_SCENARIO", str(tmp_path / "scenario.json"))
    monkeypatch.setenv("FAKE_LAKE_LOG", str(tmp_path / "log.jsonl"))
    monkeypatch.setattr("story_maker.formal.lean_ci.LAKE", (sys.executable, str(FAKE_LAKE)))
    result_json = tmp_path / "resultado.json"

    code = main(["compilar", str(lean_dir), str(tmp_path / "Cronologia.lean"), str(result_json)])

    assert code == 0
    lean_row.check(interpret(read_result(zip_of(result_json))))


def test_the_ci_commands_run_with_the_standard_library_alone(tmp_path: Path) -> None:
    """Sin site-packages (`-S`): el job formal y el workflow no instalan el backend."""
    src = Path(__file__).resolve().parents[2] / "src"
    env = {**os.environ, "PYTHONPATH": str(src), "FICHERO": encode_input(SOURCE)}
    target = tmp_path / "Cronologia.lean"

    run = subprocess.run(
        [
            sys.executable,
            "-S",
            "-m",
            "story_maker.formal.lean_ci",
            "decodificar",
            str(target),
            str(tmp_path / "resultado.json"),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert run.returncode == 0, run.stderr
    assert target.read_text(encoding="utf-8") == SOURCE

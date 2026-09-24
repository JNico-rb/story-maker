"""Modo local del `VerificadorFormal` con un sustituto de `lake` (007-C13, 007-I7)."""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from story_maker.formal.local import LocalFormalVerifier
from story_maker.formal.result import ChronologyResult, VerifierInterruption
from story_maker.settings import ROOT

FAKE_LAKE = Path(__file__).with_name("fake_lake.py")
SOURCE = "import Chronology\n\n-- fichero de prueba\n"


@pytest.fixture
def lab(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    """Directorio de datos vacío, copia de `lean/` y ficheros del sustituto, cada uno aparte."""
    lean_dir = tmp_path / "repo-lean"
    lean_dir.mkdir()
    for name in ("Chronology.lean", "lakefile.toml", "lean-toolchain", "lake-manifest.json"):
        shutil.copy2(ROOT / "lean" / name, lean_dir / name)
    paths = {
        "data": tmp_path / "data",
        "lean": lean_dir,
        "scenario": tmp_path / "fake" / "scenario.json",
        "log": tmp_path / "fake" / "log.jsonl",
        "pids": tmp_path / "fake" / "pids.txt",
    }
    paths["data"].mkdir()
    paths["scenario"].parent.mkdir()
    monkeypatch.setenv("FAKE_LAKE_SCENARIO", str(paths["scenario"]))
    monkeypatch.setenv("FAKE_LAKE_LOG", str(paths["log"]))
    monkeypatch.setenv("FAKE_LAKE_PIDS", str(paths["pids"]))
    return paths


def program(lab: dict[str, Path], **steps: dict[str, Any]) -> None:
    lab["scenario"].write_text(json.dumps(steps), encoding="utf-8")


def verifier(lab: dict[str, Path], timeout: float = 30) -> LocalFormalVerifier:
    return LocalFormalVerifier(
        data_dir=lab["data"],
        timeout_seconds=timeout,
        lean_dir=lab["lean"],
        lake=(sys.executable, str(FAKE_LAKE)),
    )


def calls(lab: dict[str, Path]) -> list[dict[str, Any]]:
    lines = lab["log"].read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines]


def snapshot(root: Path) -> dict[str, float]:
    return {str(p.relative_to(root)): p.stat().st_mtime for p in root.rglob("*")}


def inside(path: str | Path, root: Path) -> bool:
    return Path(path).resolve().is_relative_to(root.resolve())


async def test_the_local_mode_compiles_in_the_data_dir_and_interprets_the_output(
    lab: dict[str, Path], lean_row: Any
) -> None:
    program(lab, lean={"exit_code": lean_row.output.exit_code, "output": lean_row.output.output})
    lean_before = snapshot(lab["lean"])

    result = await verifier(lab).verify(SOURCE)

    assert isinstance(result, ChronologyResult)
    lean_row.check(result)
    made = calls(lab)
    assert [c["args"][:2] for c in made] == [["build", "--wfail"], ["env", "lean"]]
    assert all(inside(c["cwd"], lab["data"]) for c in made)
    compiled = Path(made[-1]["args"][-1])
    assert "-DwarningAsError=true" in made[-1]["args"]
    assert inside(compiled, lab["data"])
    assert compiled.read_text(encoding="utf-8") == SOURCE
    assert snapshot(lab["lean"]) == lean_before
    outside = {p.name for p in lab["data"].parent.iterdir()}
    assert outside == {"data", "repo-lean", "fake"}


async def test_a_library_that_does_not_build_is_an_error_with_its_first_diagnostic(
    lab: dict[str, Path],
) -> None:
    program(lab, build={"exit_code": 1, "output": "Chronology.lean:3:0: error: boom\n"})

    result = await verifier(lab).verify(SOURCE)

    assert isinstance(result, ChronologyResult)
    assert result.result == "error"
    assert result.reason is not None
    assert "boom" in result.reason
    assert [c["args"][0] for c in calls(lab)] == ["build"]


async def test_a_compile_command_that_does_not_exist_gives_no_verdict_unreachable(
    lab: dict[str, Path],
) -> None:
    missing = LocalFormalVerifier(
        data_dir=lab["data"],
        timeout_seconds=30,
        lean_dir=lab["lean"],
        lake=("sm-lake-que-no-existe",),
    )

    result = await missing.verify(SOURCE)

    assert isinstance(result, VerifierInterruption)
    assert result.reason == "verifier_unreachable"


def is_alive(pid: int) -> bool:
    if sys.platform == "win32":
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
            return code.value == 259  # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    stat = Path(f"/proc/{pid}/stat")
    return not (stat.exists() and stat.read_text().rsplit(")", 1)[-1].split()[0] == "Z")


def wait_dead(pid: int, seconds: float = 10) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if not is_alive(pid):
            return True
        time.sleep(0.1)
    return False


async def test_a_compilation_past_the_timeout_gives_no_verdict_and_no_process_survives(
    lab: dict[str, Path],
) -> None:
    program(lab, lean={"exit_code": 0, "output": "", "sleep": 60})
    started = time.monotonic()

    result = await verifier(lab, timeout=2).verify(SOURCE)

    assert isinstance(result, VerifierInterruption)
    assert result.reason == "verifier_timeout"
    assert time.monotonic() - started < 30
    pids = [int(pid) for pid in lab["pids"].read_text(encoding="utf-8").split()]
    assert len(pids) == 2
    assert all(wait_dead(pid) for pid in pids)

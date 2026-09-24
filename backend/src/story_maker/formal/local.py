"""`VerificadorFormal` en modo `local`: `lake` en esta máquina (Linux o CI).

Todo ocurre en el directorio de datos (007-I7): allí se copia la biblioteca `lean/` (lo que
construye Lake queda allí también), allí se escribe el fichero y allí corre la compilación. Es la
misma verificación que el workflow de GitHub (007-I9): `lake build --wfail` de la biblioteca y
`lean -DwarningAsError=true` del fichero, con la auditoría de axiomas que el fichero lleva dentro.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from story_maker.formal.lean_output import LeanOutput, interpret
from story_maker.formal.result import VerificationOutcome, VerifierInterruption
from story_maker.settings import ROOT

LEAN_DIR = ROOT / "lean"
LIBRARY_FILES = ("Chronology.lean", "lakefile.toml", "lean-toolchain", "lake-manifest.json")


class CompileTimeout(Exception):
    """La compilación no terminó a tiempo; sus procesos ya están muertos."""


def sync_library(lean_dir: Path, workspace: Path) -> None:
    """Copia la biblioteca al espacio de trabajo, solo lo que cambió (Lake conserva su caché)."""
    sources = [lean_dir / name for name in LIBRARY_FILES]
    if (lean_dir / "Chronology").is_dir():
        sources += sorted((lean_dir / "Chronology").rglob("*.lean"))
    for source in sources:
        target = workspace / source.relative_to(lean_dir)
        content = source.read_bytes()
        if not target.is_file() or target.read_bytes() != content:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)


def _kill_tree(process: subprocess.Popen[bytes]) -> None:
    """Mata el proceso y sus hijos: Lake lanza `lean` como hijo."""
    if sys.platform == "win32":
        # taskkill viene con Windows; /T recorre el árbol de procesos.
        subprocess.run(  # noqa: S603
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],  # noqa: S607
            capture_output=True,
            check=False,
        )
    else:
        import os
        import signal

        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
    process.kill()
    with contextlib.suppress(subprocess.TimeoutExpired):
        process.communicate(timeout=5)


def _run(args: Sequence[str], cwd: Path, deadline: float) -> LeanOutput:
    """Lanza `args` sin shell; `OSError` si la orden no existe o no arranca."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise CompileTimeout
    if sys.platform == "win32":
        process = subprocess.Popen(  # noqa: S603 — argumentos fijos, sin shell
            list(args),
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    else:
        process = subprocess.Popen(  # noqa: S603 — argumentos fijos, sin shell
            list(args),
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,  # su propio grupo, para matar el árbol entero
        )
    try:
        output, _ = process.communicate(timeout=remaining)
    except subprocess.TimeoutExpired:
        _kill_tree(process)
        raise CompileTimeout from None
    return LeanOutput(process.returncode, output.decode("utf-8", errors="replace"))


def compile_file(
    workspace: Path, file: Path, lake: Sequence[str], timeout_seconds: float
) -> LeanOutput:
    """Construye la biblioteca con `--wfail` y compila `file` contra ella, en `workspace`."""
    deadline = time.monotonic() + timeout_seconds
    build = _run([*lake, "build", "--wfail"], workspace, deadline)
    if build.exit_code != 0:
        return build
    return _run([*lake, "env", "lean", "-DwarningAsError=true", str(file)], workspace, deadline)


class LocalFormalVerifier:
    def __init__(
        self,
        data_dir: Path,
        timeout_seconds: float,
        lean_dir: Path = LEAN_DIR,
        lake: Sequence[str] = ("lake",),
    ) -> None:
        self.data_dir = data_dir
        self.timeout_seconds = timeout_seconds
        self.lean_dir = lean_dir
        self.lake = tuple(lake)

    async def verify(self, source: str) -> VerificationOutcome:
        return await asyncio.to_thread(self._verify, source)

    def _verify(self, source: str) -> VerificationOutcome:
        workspace = self.data_dir / "lean"
        sync_library(self.lean_dir, workspace)
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
        file = workspace / f"Cronologia_{digest}.lean"
        file.write_bytes(source.encode("utf-8"))
        try:
            output = compile_file(workspace, file, self.lake, self.timeout_seconds)
        except CompileTimeout:
            return VerifierInterruption(
                "verifier_timeout", f"la compilación pasó de {self.timeout_seconds} s"
            )
        except OSError as exc:
            return VerifierInterruption(
                "verifier_unreachable", f"la orden de compilación no arranca ({type(exc).__name__})"
            )
        return interpret(output)

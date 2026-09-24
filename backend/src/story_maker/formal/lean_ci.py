"""Órdenes de la verificación Lean fuera del servidor: el job formal de la CI y el workflow
`LEAN_WORKFLOW` del modo github. Solo usan la biblioteca estándar, así que corren sin instalar el
backend: `PYTHONPATH=backend/src python3 -m story_maker.formal.lean_ci <orden> ...`.

- `pruebas <lean_dir>`: compila cada fichero de `<lean_dir>/pruebas` y lo compara con
  `esperado.json` (007-C20 a 007-C24). Sale con 1 si alguno no da lo esperado.
- `decodificar <fichero.lean> <resultado.json>`: lee el input `FICHERO` del entorno, comprueba
  que es base64 y gzip antes de descomprimirlo y escribe el fichero. Si no es válido, escribe un
  resultado de error y no deja nada que compilar. Anota `valido` en `GITHUB_OUTPUT`.
- `compilar <lean_dir> <fichero.lean> <resultado.json>`: compila como el modo local (la misma
  orden, 007-I9) y escribe la salida, que el modo github lee del artefacto.
"""

from __future__ import annotations

import base64
import binascii
import json
import os
import sys
import zlib
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from story_maker.formal.lean_output import (
    LeanOutput,
    audit_problems,
    first_diagnostic,
    interpret,
    parse_audit,
)
from story_maker.formal.local import CompileTimeout, compile_file

LAKE: tuple[str, ...] = ("lake",)
# Un fichero de cronología real ocupa decenas de KB; más de esto es un input malicioso.
MAX_SOURCE_BYTES = 2_000_000
# Por debajo del tope del job del workflow, para que siempre haya artefacto.
COMPILE_TIMEOUT_SECONDS = 840
INVALID_INPUT_EXIT = 2


class InvalidInput(ValueError):
    """El input del workflow no es un fichero en gzip y base64."""


def decode_input(value: str) -> str:
    """El fichero que viaja en el input: base64 estricto, gzip con tope de tamaño y UTF-8."""
    try:
        compressed = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        raise InvalidInput("el input no es base64") from None
    if compressed[:2] != b"\x1f\x8b":
        raise InvalidInput("el input no es gzip")
    decompressor = zlib.decompressobj(wbits=31)
    try:
        data = decompressor.decompress(compressed, MAX_SOURCE_BYTES)
    except zlib.error:
        raise InvalidInput("el gzip del input está dañado") from None
    if decompressor.unconsumed_tail:
        raise InvalidInput(f"el fichero pasa de {MAX_SOURCE_BYTES} bytes")
    if not decompressor.eof:
        raise InvalidInput("el gzip del input está incompleto")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise InvalidInput("el fichero no es UTF-8") from None


def _witnesses(witnesses: Iterable[tuple[str, tuple[int, ...]]]) -> str:
    return ", ".join(f"{t} {w}" for t, w in sorted(witnesses)) or "ninguno"


def check_expectation(expectation: dict[str, Any], lean: LeanOutput) -> str | None:
    """Qué no cumple `lean` de lo que la CI espera, o nada si lo cumple todo."""
    if "auditoria" in expectation:
        if lean.exit_code != 0:
            return f"no compila: {first_diagnostic(lean.output)}"
        problems = audit_problems(parse_audit(lean.output), list(expectation["auditoria"]))
        return "; ".join(problems) or None
    result = interpret(lean)
    problems = []
    if result.result != expectation["resultado"]:
        detail = f" ({result.reason})" if result.reason else ""
        problems.append(f"se esperaba {expectation['resultado']} y da {result.result}{detail}")
    wanted = {t: tuple(w) for t, w in expectation.get("testigos", {}).items()}
    if expectation["resultado"] == "failed" and dict(result.witnesses) != wanted:
        got = _witnesses(result.witnesses.items())
        problems.append(f"se esperaban los testigos {_witnesses(wanted.items())} y da {got}")
    compiles = lean.exit_code == 0
    if "compila" in expectation and compiles != expectation["compila"]:
        problems.append("compila y no debía" if compiles else "no compila y debía")
    for fragment in expectation.get("motivo", []):
        if fragment not in (result.reason or ""):
            problems.append(f"el motivo no nombra {fragment}: {result.reason}")
    return "; ".join(problems) or None


def run_ci_files(
    lean_dir: Path, lake: tuple[str, ...] = LAKE, timeout: float = COMPILE_TIMEOUT_SECONDS
) -> int:
    """Compila cada fichero de `pruebas/` contra la biblioteca y lo compara con lo esperado."""
    lean_dir = lean_dir.resolve()
    pruebas = lean_dir / "pruebas"
    expected = json.loads((pruebas / "esperado.json").read_text(encoding="utf-8"))
    failures = 0
    for name in sorted(set(expected) | {p.name for p in pruebas.glob("*.lean")}):
        path = pruebas / name
        if name not in expected or not path.is_file():
            problem: str | None = "sin expectativa" if name not in expected else "no existe"
        else:
            try:
                problem = check_expectation(
                    expected[name], compile_file(lean_dir, path, lake, timeout)
                )
            except CompileTimeout:
                problem = f"no termina en {timeout} s"
            except OSError as exc:
                problem = f"la orden de compilación no arranca ({type(exc).__name__})"
        failures += problem is not None
        print(f"FALLO {name}: {problem}" if problem else f"OK {name}")
    return 1 if failures else 0


def _write_result(path: Path, lean: LeanOutput) -> None:
    payload = {"exit_code": lean.exit_code, "output": lean.output}
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _set_output(key: str, value: str) -> None:
    target = os.environ.get("GITHUB_OUTPUT")
    if target:
        with Path(target).open("a", encoding="utf-8") as output:
            output.write(f"{key}={value}\n")


def _decode(target: Path, result: Path) -> int:
    try:
        source = decode_input(os.environ.get("FICHERO", ""))
    except InvalidInput as exc:
        _write_result(result, LeanOutput(INVALID_INPUT_EXIT, f"input inválido: {exc}"))
        _set_output("valido", "false")
        return 0
    target.write_bytes(source.encode("utf-8"))
    _set_output("valido", "true")
    return 0


def _compile(lean_dir: Path, source: Path, result: Path) -> int:
    try:
        lean = compile_file(lean_dir.resolve(), source.resolve(), LAKE, COMPILE_TIMEOUT_SECONDS)
    except CompileTimeout:
        lean = LeanOutput(124, f"la compilación pasó de {COMPILE_TIMEOUT_SECONDS} s")
    except OSError as exc:
        lean = LeanOutput(127, f"la orden de compilación no arranca ({type(exc).__name__})")
    _write_result(result, lean)
    return 0


def main(argv: list[str] | None = None) -> int:
    match sys.argv[1:] if argv is None else argv:
        case ["pruebas", lean_dir]:
            return run_ci_files(Path(lean_dir), LAKE)
        case ["decodificar", target, result]:
            return _decode(Path(target), Path(result))
        case ["compilar", lean_dir, source, result]:
            return _compile(Path(lean_dir), Path(source), Path(result))
        case _:
            print(__doc__, file=sys.stderr)
            return 2


if __name__ == "__main__":
    sys.exit(main())

"""Verify a chronology with Lean and write the result JSON of lean/README.md.

    python3 scripts/verify.py --json chronology.json --result result.json
    python3 scripts/verify.py --encoded-env CHRONOLOGY --result result.json
    python3 scripts/verify.py --examples examples

Run from lean/, with `lake` on the PATH. Exit code: 0 when the four invariants hold, 1 when one
fails, 2 when the verification could not run. With --examples, 0 only if every example gives
what examples/expected.json says and the audit rejects every seed in examples/seeds/.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import generate

LEAN = Path(__file__).resolve().parent.parent
DATA_FILE = LEAN / "Input" / "Data.lean"
SEED_FILE = LEAN / "Input" / "Seeded.lean"
INVARIANTS = ["t1-orden", "t2-edad", "t3-dos-lugares", "t4-excluyente"]
RESULT_VERSION = 1
BUILD_SECONDS = 900
AUDIT_REJECTION = "which is not a standard axiom"


def error_result(message: str) -> dict:
    return {
        "version": RESULT_VERSION, "status": "error", "invariant": None, "witness": None,
        "invariants": [], "error": message,
    }


def exit_code(result: dict) -> int:
    return {"pass": 0, "fail": 1}.get(result["status"], 2)


def combine(proved: bool, entries: object) -> dict:
    """The verdict: the theorems of Input.Proofs decide it, and the report names the witness."""
    if not _well_formed(entries):
        return error_result("the report of scripts/Report.lean is malformed")
    assert isinstance(entries, list)
    violations = [entry for entry in entries if not entry["holds"]]
    if proved and not violations:
        status, first = "pass", None
    elif not proved and violations:
        status, first = "fail", violations[0]
    elif proved:
        return error_result("the theorems hold but the report finds a violation")
    else:
        return error_result("the theorems failed but the report finds no violation: see the build log")
    return {
        "version": RESULT_VERSION, "status": status,
        "invariant": None if first is None else first["invariant"],
        "witness": None if first is None else first["witness"],
        "invariants": entries, "error": None,
    }


def _well_formed(entries: object) -> bool:
    if not isinstance(entries, list) or [e.get("invariant") if isinstance(e, dict) else None for e in entries] != INVARIANTS:
        return False
    for entry in entries:
        witness = entry.get("witness")
        if not isinstance(entry.get("holds"), bool):
            return False
        if entry["holds"] != (witness is None):
            return False
        if witness is not None and (
            not isinstance(witness, dict) or set(witness) != {"events", "characters"}
            or not all(isinstance(ids, list) and all(isinstance(i, int) for i in ids) for ids in witness.values())
        ):
            return False
    return True


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    print("$ " + " ".join(command), flush=True)
    completed = subprocess.run(
        command, cwd=LEAN, capture_output=True, text=True, timeout=BUILD_SECONDS, check=False,
    )
    sys.stdout.write(completed.stdout)
    sys.stdout.write(completed.stderr)
    return completed


def verify(data: object) -> dict:
    """Generate Input/Data.lean, build Input.Proofs and join its verdict with the report."""
    try:
        chronology = generate.parse(data)
    except generate.ChronologyError as error:
        return error_result(f"invalid chronology: {error}")
    DATA_FILE.write_text(generate.render(chronology), encoding="utf-8")
    try:
        proofs = _run(["lake", "build", "--wfail", "Input.Proofs"])
        report = _run(["lake", "env", "lean", "--run", "scripts/Report.lean"])
    except (OSError, subprocess.TimeoutExpired) as error:
        return error_result(f"Lean did not run: {error}")
    if report.returncode != 0:
        return error_result("scripts/Report.lean did not run: see the build log")
    try:
        entries = json.loads(report.stdout)
    except json.JSONDecodeError:
        return error_result("the report of scripts/Report.lean is not JSON")
    return combine(proofs.returncode == 0, entries)


def check_examples(folder: Path) -> int:
    """Every example against examples/expected.json, then every seed against the audit."""
    expected = json.loads((folder / "expected.json").read_text(encoding="utf-8"))
    failures = []
    for name, want in expected.items():
        print(f"=== {name}", flush=True)
        result = verify(json.loads((folder / name).read_text(encoding="utf-8")))
        got = {key: result[key] for key in want}
        failing = [e["invariant"] for e in result["invariants"] if not e["holds"]]
        if got != want or failing != ([want["invariant"]] if "invariant" in want else []):
            failures.append(f"{name}: expected {want}, got {json.dumps(result)}")
    verify(json.loads((folder / "positive.json").read_text(encoding="utf-8")))
    for seed in sorted((folder / "seeds").glob("*.lean")):
        print(f"=== seed {seed.name}", flush=True)
        shutil.copyfile(seed, SEED_FILE)
        try:
            build = _run(["lake", "build", "Input.Seeded"])
        finally:
            SEED_FILE.unlink()
        if build.returncode == 0 or AUDIT_REJECTION not in build.stdout + build.stderr:
            failures.append(f"seed {seed.name}: the audit did not reject it")
    for failure in failures:
        print(f"FAILED {failure}", flush=True)
    print(f"{len(expected)} examples and the seeds: {'all as expected' if not failures else f'{len(failures)} failures'}")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--json", type=Path, help="a chronology JSON file")
    source.add_argument("--encoded-env", help="an environment variable holding the chronology, gzip + base64")
    source.add_argument("--examples", type=Path, help="the folder with the examples and expected.json")
    parser.add_argument("--result", type=Path, help="where to write the result JSON")
    args = parser.parse_args(argv[1:])
    if args.examples is not None:
        return check_examples(args.examples)
    try:
        if args.json is not None:
            data = json.loads(args.json.read_text(encoding="utf-8"))
        else:
            data = generate.decode(os.environ.get(args.encoded_env, ""))
        result = verify(data)
    except (OSError, json.JSONDecodeError, generate.ChronologyError) as error:
        result = error_result(f"invalid chronology: {error}")
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.result is not None:
        args.result.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return exit_code(result)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

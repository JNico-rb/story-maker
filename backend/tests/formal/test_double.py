"""Doble del `VerificadorFormal` (007-C19)."""

from __future__ import annotations

import socket
import subprocess
from typing import Any, NoReturn

import pytest

from story_maker.formal.double import ProgrammedFormalVerifier
from story_maker.formal.result import ChronologyResult, VerificationOutcome, VerifierInterruption

ALL_HOLD = dict.fromkeys(("T1", "T2", "T3", "T4", "T5"), True)
PROGRAMMED: list[VerificationOutcome] = [
    ChronologyResult("passed", holds=ALL_HOLD),
    ChronologyResult(
        "failed",
        holds={**ALL_HOLD, "T1": False, "T4": False},
        witnesses={"T1": (43, 44), "T4": (12, 32, 71)},
    ),
    ChronologyResult("error", reason="no compila"),
    VerifierInterruption("verifier_unreachable"),
    VerifierInterruption("verifier_timeout"),
]


def forbidden(*_: Any, **__: Any) -> NoReturn:
    raise AssertionError("el doble no abre conexiones ni lanza procesos")


async def test_the_double_returns_what_was_programmed_without_network_or_lean(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    double = ProgrammedFormalVerifier(PROGRAMMED)
    # Ni siquiera son ficheros Lean: el doble no evalúa nada, solo devuelve lo programado.
    sources = [f"fichero {n}" for n in range(len(PROGRAMMED))]

    results = [await double.verify(source) for source in sources]

    assert all(got is want for got, want in zip(results, PROGRAMMED, strict=True))
    assert double.received == sources


async def test_the_double_refuses_a_verification_it_was_not_programmed_for() -> None:
    double = ProgrammedFormalVerifier([ChronologyResult("passed", holds=ALL_HOLD)])
    await double.verify("uno")

    with pytest.raises(LookupError):
        await double.verify("dos")

"""Doble determinista del `VerificadorFormal` para las pruebas de quien lo consume (012, 019).

Devuelve, en orden, los resultados con que se programa y guarda los ficheros que recibe. No abre
conexiones, no lanza procesos y no evalúa ningún invariante (007-I1).
"""

from __future__ import annotations

from collections.abc import Iterable

from story_maker.formal.result import VerificationOutcome


class ProgrammedFormalVerifier:
    def __init__(self, outcomes: Iterable[VerificationOutcome]) -> None:
        self._pending = list(outcomes)
        self.received: list[str] = []

    async def verify(self, source: str) -> VerificationOutcome:
        if not self._pending:
            raise LookupError("el doble del VerificadorFormal no tiene más resultados programados")
        self.received.append(source)
        return self._pending.pop(0)

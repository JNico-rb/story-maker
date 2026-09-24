"""`TechoDeTokens`: contador global en memoria de los tokens en vuelo (`architecture.md` §6.5)."""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field


def estimate_tokens(chars: int) -> int:
    """Estimador local chars/4, redondeando hacia arriba."""
    return -(-chars // 4)


def reservation(input_chars: int, max_turns: int, max_output_tokens: int) -> int:
    """Entrada estimada más el crecimiento de los turnos que siguen al primero."""
    return estimate_tokens(input_chars) + (max_turns - 1) * max_output_tokens


@dataclass(eq=False)
class Ticket:
    amount: int
    granted: bool = False
    released: bool = False
    _granted_event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)


class TokenCeiling:
    """Un solo proceso, un solo contador (§1.4); las reservas se atienden en orden de llegada."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.in_use = 0
        self._queue: deque[Ticket] = deque()

    async def acquire(self, amount: int, timeout: float | None) -> Ticket:
        ticket = Ticket(amount)
        self._queue.append(ticket)
        self._grant()
        await ticket._granted_event.wait()
        return ticket

    def release(self, ticket: Ticket) -> None:
        ticket.released = True
        self.in_use -= ticket.amount
        self._grant()

    def _grant(self) -> None:
        # Estricto en orden de llegada: una pequeña no adelanta a una grande que llegó antes.
        while self._queue and self.in_use + self._queue[0].amount <= self.limit:
            ticket = self._queue.popleft()
            ticket.granted = True
            self.in_use += ticket.amount
            ticket._granted_event.set()

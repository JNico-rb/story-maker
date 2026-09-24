"""`TechoDeTokens`: contador global en memoria de los tokens en vuelo (`architecture.md` §6.5)."""

from __future__ import annotations

from dataclasses import dataclass


def estimate_tokens(chars: int) -> int:
    """Estimador local chars/4, redondeando hacia arriba."""
    return -(-chars // 4)


def reservation(input_chars: int, max_turns: int, max_output_tokens: int) -> int:
    """Entrada estimada más el crecimiento de los turnos que siguen al primero."""
    return estimate_tokens(input_chars) + (max_turns - 1) * max_output_tokens


@dataclass
class Ticket:
    amount: int


class TokenCeiling:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.in_use = 0

    async def acquire(self, amount: int, timeout: float | None) -> Ticket:
        self.in_use += amount
        return Ticket(amount)

    def release(self, ticket: Ticket) -> None:
        self.in_use -= ticket.amount

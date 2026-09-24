"""Uso de una sesión y su coste a precio de lista (`architecture.md` §13.2)."""

from __future__ import annotations

from dataclasses import dataclass

from story_maker.config import PriceConfig


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int


def cost_usd(usage: Usage, price: PriceConfig) -> float:
    """Uso real por `operation.pricing` del modelo, en USD por millón de tokens."""
    return (
        usage.input_tokens * price.input
        + usage.output_tokens * price.output
        + usage.cache_read_tokens * price.cache_read
        + usage.cache_write_tokens * price.cache_write
    ) / 1_000_000

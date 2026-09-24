"""Selección de adaptador: con las cuatro variables de Langfuse, el real; si no, el doble nulo."""

from __future__ import annotations

from typing import cast

from story_maker.observability.langfuse_client import LangfuseClientPort
from story_maker.settings import Settings


def has_langfuse_vars(settings: Settings) -> bool:
    """Las cuatro variables de Langfuse a la vez; falta una y ya no cuenta (004-C02, 004-I2)."""
    return bool(
        settings.langfuse_public_key
        and settings.langfuse_secret_key
        and settings.langfuse_base_url
        and settings.langfuse_prompt_label
    )


def build_langfuse_client(settings: Settings) -> LangfuseClientPort:
    """Cliente real; solo se llama cuando `has_langfuse_vars` ya dio cierto (004-C01).

    `Langfuse` (v4) cubre `LangfuseClientPort` de sobra: sus overloads de
    `start_as_current_observation` (una por `as_type`) devuelven tipos más concretos que el
    puerto estrecho que usa el adaptador, así que mypy no lo ve estructuralmente compatible."""
    from langfuse import Langfuse  # importado aquí: solo cuando de verdad se usa Langfuse

    client = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        base_url=settings.langfuse_base_url,
    )
    return cast(LangfuseClientPort, client)

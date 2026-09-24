"""Selección del cliente real: las cuatro variables y nunca una conexión real en pruebas T."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import httpx
import pytest
from tests.conftest import BlockedOutboundConnection

from story_maker.observability.factory import build_langfuse_client, has_langfuse_vars
from story_maker.settings import Settings


def _settings_with_langfuse(base_url: str) -> Settings:
    return Settings(
        data_dir=Path("."),
        config_path=Path("config.json"),
        base_url="http://127.0.0.1:8000",
        frontend_dist=Path("."),
        jwt_secret="x" * 32,
        llm_provider="claude_login",
        formal_verifier="local",
        github_repository=None,
        lean_workflow=None,
        github_token=None,
        claude_code_oauth_token=None,
        anthropic_base_url=None,
        anthropic_auth_token=None,
        openrouter_api_key=None,
        langfuse_public_key="pk-marcador-prueba",
        langfuse_secret_key="sk-marcador-prueba",
        langfuse_base_url=base_url,
        langfuse_prompt_label="produccion",
    )


def test_has_langfuse_vars_is_true_only_with_the_four_present() -> None:
    complete = _settings_with_langfuse("http://93.184.216.34:9999")
    assert has_langfuse_vars(complete) is True
    assert has_langfuse_vars(replace(complete, langfuse_prompt_label=None)) is False


# --- I7: ninguna llamada real a modelo o Langfuse en una prueba T ------------------------------


def test_the_real_clients_auth_check_is_stopped_by_the_outbound_network_guard() -> None:
    """Si algún día un test olvida inyectar el cliente simulado, la red bloqueada lo frena (I7)."""
    settings = _settings_with_langfuse("http://93.184.216.34:9999")
    client = build_langfuse_client(settings)

    with pytest.raises(httpx.ConnectError) as excinfo:
        client.auth_check()

    # httpx envuelve el error de bajo nivel de httpcore, que a su vez encadena el nuestro.
    httpcore_error = excinfo.value.__cause__
    assert isinstance(httpcore_error.__context__, BlockedOutboundConnection)

"""`LangfuseObservability`: mismo contrato que el doble nulo, get_prompt real y exportación."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from tests.conftest import FakeLangfuseClient

from story_maker.observability import langfuse_adapter
from story_maker.observability.langfuse_adapter import LangfuseObservability

LABEL = "produccion"


# --- C09: al arrancar, cada LlamadaDeModelo enlaza la versión leída por la etiqueta -----------


def test_get_prompt_answers_the_current_version_instead_of_none(
    fake_langfuse_client: FakeLangfuseClient,
) -> None:
    fake_langfuse_client.register_prompt("writer", LABEL, version=3)
    observability = LangfuseObservability(fake_langfuse_client)

    version = observability.get_prompt("writer", LABEL)

    assert version == "3"


def test_get_prompt_of_a_role_without_a_version_under_that_label_answers_none(
    fake_langfuse_client: FakeLangfuseClient,
) -> None:
    observability = LangfuseObservability(fake_langfuse_client)

    assert observability.get_prompt("writer", LABEL) is None


# --- 003-C25: el coste del SDK viaja en la LlamadaDeModelo solo como contraste (§18) ----------


def test_the_sdk_cost_is_exported_as_contrast_metadata_and_not_as_the_cost(
    fake_langfuse_client: FakeLangfuseClient,
) -> None:
    observability = LangfuseObservability(fake_langfuse_client)
    with (
        observability.trace("run:1") as trace,
        observability.span(trace, "rol:writer") as span,
    ):
        observability.model_call(span, model="claude-sonnet-5", cost_usd=0.08, sdk_cost_usd=20.0)
    observability.flush()

    (exported_span,) = fake_langfuse_client.roots["trace-run:1"].children
    (generation,) = exported_span.children
    assert generation.cost_details == {"total": 0.08}
    assert generation.metadata is not None
    assert generation.metadata["sdk_cost_usd"] == 20.0


# --- 004 §13.1: una sesión por novela — la traza sale con `session_id`, no solo en metadata ----


def test_a_trace_with_a_session_is_exported_with_that_langfuse_session_id(
    fake_langfuse_client: FakeLangfuseClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    propagated: list[str | None] = []

    @contextmanager
    def fake_propagate(*, session_id: str | None = None) -> Iterator[None]:
        propagated.append(session_id)
        yield

    monkeypatch.setattr(langfuse_adapter, "propagate_attributes", fake_propagate)
    observability = LangfuseObservability(fake_langfuse_client)
    with (
        observability.trace("run:1", name="generacion", session="7") as trace,
        observability.span(trace, "rol:writer"),
    ):
        pass
    observability.flush()

    assert propagated == ["7"]


def test_a_trace_without_a_session_is_exported_without_a_session_id(
    fake_langfuse_client: FakeLangfuseClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    propagated: list[str | None] = []

    @contextmanager
    def fake_propagate(*, session_id: str | None = None) -> Iterator[None]:
        propagated.append(session_id)
        yield

    monkeypatch.setattr(langfuse_adapter, "propagate_attributes", fake_propagate)
    observability = LangfuseObservability(fake_langfuse_client)
    with observability.trace("mcp:list_novels"):
        pass
    observability.flush()

    assert propagated == []

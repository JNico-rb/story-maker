"""El puerto de observabilidad declara todo lo que emiten sus dos adaptadores (001-C19..C21, 004).

Quien emite telemetría (el puerto de agente, 003) tipa contra `ObservabilityPort`, no contra
un adaptador."""

from __future__ import annotations

import inspect

import pytest

from story_maker.observability.langfuse_adapter import LangfuseObservability
from story_maker.observability.null import NullObservability
from story_maker.observability.port import ObservabilityPort

OPERATIONS = ("trace", "span", "model_call", "score", "get_prompt", "check", "flush")


def shape(function: object) -> list[tuple[str, object, object]]:
    return [
        (p.name, p.kind, p.default)
        for p in inspect.signature(function).parameters.values()  # type: ignore[arg-type]
    ]


@pytest.mark.parametrize("adapter", [NullObservability, LangfuseObservability])
@pytest.mark.parametrize("operation", OPERATIONS)
def test_the_port_declares_each_operation_with_the_signature_of_its_adapters(
    operation: str, adapter: type
) -> None:
    declared = getattr(ObservabilityPort, operation, None)

    assert declared is not None, f"ObservabilityPort no declara {operation}"
    assert shape(declared) == shape(getattr(adapter, operation))

"""Fixtures compartidas: red saliente bloqueada salvo 127.0.0.1 (001-I3); cliente de Langfuse
simulado por fixture, sin red (004, `verification.md` §3.3)."""

from __future__ import annotations

import socket
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

import pytest

_REAL_CONNECT = socket.socket.connect
_REAL_CONNECT_EX = socket.socket.connect_ex
_ALLOWED_HOSTS = {"127.0.0.1", "::1", "localhost"}


class BlockedOutboundConnection(OSError):
    """Una prueba intentó abrir una conexión fuera de la máquina (I3)."""


def _host_of(address: object) -> object:
    return address[0] if isinstance(address, tuple) else address


def guarded_connect(self: socket.socket, address: object) -> None:
    host = _host_of(address)
    if host not in _ALLOWED_HOSTS:
        raise BlockedOutboundConnection(f"red saliente bloqueada en las pruebas (I3): {host!r}")
    _REAL_CONNECT(self, address)


def guarded_connect_ex(self: socket.socket, address: object) -> int:
    host = _host_of(address)
    if host not in _ALLOWED_HOSTS:
        raise BlockedOutboundConnection(f"red saliente bloqueada en las pruebas (I3): {host!r}")
    return _REAL_CONNECT_EX(self, address)


@pytest.fixture(autouse=True, scope="session")
def _block_outbound_network() -> Iterator[None]:
    socket.socket.connect = guarded_connect  # type: ignore[method-assign]
    socket.socket.connect_ex = guarded_connect_ex  # type: ignore[method-assign]
    try:
        yield
    finally:
        socket.socket.connect = _REAL_CONNECT  # type: ignore[method-assign]
        socket.socket.connect_ex = _REAL_CONNECT_EX  # type: ignore[method-assign]


# --- Cliente de Langfuse simulado (004) ------------------------------------------------------
#
# Dobla el subconjunto real de `langfuse.Langfuse` (v4) que usa el adaptador: responde a la
# comprobación de credenciales, a la consulta de un prompt por etiqueta y captura lo exportado,
# igual que hace el doble nulo de 001-base con lo emitido por el puerto. Sin red (004-I2, 004-I7).


@dataclass
class FakePrompt:
    version: int
    config: dict[str, Any] = field(default_factory=dict)
    text: str = ""


@dataclass
class FakeObservation:
    id: str
    name: str
    as_type: str
    client: FakeLangfuseClient
    input: Any = None
    output: Any = None
    metadata: dict[str, Any] | None = None
    level: str = "DEFAULT"
    status_message: str | None = None
    model: str | None = None
    usage_details: dict[str, int] | None = None
    cost_details: dict[str, float] | None = None
    children: list[FakeObservation] = field(default_factory=list)

    @contextmanager
    def start_as_current_observation(
        self, *, name: str, as_type: str = "span", **kwargs: Any
    ) -> Iterator[FakeObservation]:
        child = FakeObservation(
            id=self.client._next_id(), name=name, as_type=as_type, client=self.client, **kwargs
        )
        self.children.append(child)
        yield child


class FakeLangfuseClient:
    """Cliente de Langfuse simulado, sin red: lo que el adaptador real necesita (004)."""

    def __init__(self) -> None:
        self.auth_ok = True
        self.auth_raises: Exception | None = None
        self._prompts: dict[tuple[str, str], FakePrompt] = {}
        self.roots: dict[str, FakeObservation] = {}
        self.scores: list[dict[str, Any]] = []
        self.flush_count = 0
        self._id_counter = 0

    def _next_id(self) -> str:
        self._id_counter += 1
        return f"obs-{self._id_counter}"

    def register_prompt(
        self, name: str, label: str, *, version: int, config: dict[str, Any] | None = None
    ) -> None:
        self._prompts[(name, label)] = FakePrompt(version=version, config=config or {})

    def auth_check(self) -> bool:
        if self.auth_raises is not None:
            raise self.auth_raises
        return self.auth_ok

    def get_prompt(self, name: str, *, label: str) -> FakePrompt:
        key = (name, label)
        if key not in self._prompts:
            raise LookupError(f"no hay versión de '{name}' con la etiqueta '{label}'")
        return self._prompts[key]

    def create_prompt(
        self,
        *,
        name: str,
        prompt: str,
        labels: list[str],
        config: dict[str, Any] | None = None,
    ) -> FakePrompt:
        existing = [p.version for (n, _), p in self._prompts.items() if n == name]
        handle = FakePrompt(version=max(existing, default=0) + 1, config=config or {}, text=prompt)
        for label in labels:
            self._prompts[(name, label)] = handle
        return handle

    def create_trace_id(self, *, seed: str) -> str:
        return f"trace-{seed}"

    @contextmanager
    def start_as_current_observation(
        self,
        *,
        trace_context: dict[str, str] | None = None,
        name: str,
        as_type: str = "span",
        **kwargs: Any,
    ) -> Iterator[FakeObservation]:
        trace_id = trace_context["trace_id"] if trace_context else self.create_trace_id(seed=name)
        root = self.roots.get(trace_id)
        if root is None:
            root = FakeObservation(
                id=self._next_id(), name=name, as_type=as_type, client=self, **kwargs
            )
            self.roots[trace_id] = root
        yield root

    def create_score(
        self,
        *,
        name: str,
        value: float,
        comment: str | None = None,
        trace_id: str,
        observation_id: str | None = None,
    ) -> None:
        self.scores.append(
            {
                "name": name,
                "value": value,
                "comment": comment,
                "trace_id": trace_id,
                "observation_id": observation_id,
            }
        )

    def flush(self) -> None:
        self.flush_count += 1


@pytest.fixture
def fake_langfuse_client() -> FakeLangfuseClient:
    return FakeLangfuseClient()

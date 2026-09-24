"""Fixtures compartidas: red saliente bloqueada salvo 127.0.0.1 (001-I3)."""

from __future__ import annotations

import socket
from collections.abc import Iterator

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

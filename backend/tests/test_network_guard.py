"""Las pruebas corren con la red saliente bloqueada, salvo 127.0.0.1 (001-I3)."""

from __future__ import annotations

import socket

import pytest


def test_connecting_to_a_host_outside_the_machine_is_blocked() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(OSError, match="red saliente bloqueada"):
            sock.connect(("93.184.216.34", 80))
    finally:
        sock.close()


def test_connecting_to_127_0_0_1_is_not_blocked_by_the_guard() -> None:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = listener.getsockname()[1]

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("127.0.0.1", port))  # no lanza: la conexión local no está bloqueada
    finally:
        sock.close()
        listener.close()

"""Adaptador del puerto de agente sobre el Claude Agent SDK (`architecture.md` §7, §15.2)."""

from __future__ import annotations

import os

from story_maker.agents.port import DriverSession, SessionRequest, ToolHooks
from story_maker.agents.profiles import RoleProfile
from story_maker.settings import Settings


class RealModelInTests(RuntimeError):
    """Una prueba intentó abrir una sesión real: las pruebas T usan el doble falso (003-I6)."""


class SdkAgent:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def prepare(self, request: SessionRequest) -> None:
        # pytest fija PYTEST_CURRENT_TEST en cada prueba: así ninguna llega al CLI ni al modelo.
        if "PYTEST_CURRENT_TEST" in os.environ:
            raise RealModelInTests(
                f"sesión real de {request.role} en la suite: usa el doble falso del puerto"
            )

    def open(
        self, request: SessionRequest, profile: RoleProfile, hooks: ToolHooks
    ) -> DriverSession:
        raise NotImplementedError

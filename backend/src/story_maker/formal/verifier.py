"""El `VerificadorFormal`: su contrato y su construcción desde los ajustes (`FORMAL_VERIFIER`)."""

from __future__ import annotations

from typing import Protocol

from story_maker.formal.github import GithubFormalVerifier
from story_maker.formal.local import LocalFormalVerifier
from story_maker.formal.result import VerificationOutcome
from story_maker.settings import Settings


class FormalVerifier(Protocol):
    async def verify(self, source: str) -> VerificationOutcome:
        """Compila el `FicheroDeCronologia` `source` contra la biblioteca de invariantes."""
        ...


class FormalVerifierConfigError(ValueError):
    """Faltan ajustes del modo elegido; el mensaje solo nombra lo que falta."""


def make_formal_verifier(settings: Settings, timeout_seconds: float) -> FormalVerifier:
    """El modo de `FORMAL_VERIFIER`; `timeout_seconds` es `operation.verifier_timeout_seconds`."""
    if settings.formal_verifier != "github":
        return LocalFormalVerifier(settings.data_dir, timeout_seconds)
    required = {
        "GITHUB_REPOSITORY": settings.github_repository,
        "LEAN_WORKFLOW": settings.lean_workflow,
        "GITHUB_TOKEN": settings.github_token,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise FormalVerifierConfigError(
            f"FORMAL_VERIFIER=github exige {', '.join(missing)}, que no está definido"
        )
    return GithubFormalVerifier(
        repository=required["GITHUB_REPOSITORY"] or "",
        workflow=required["LEAN_WORKFLOW"] or "",
        token=required["GITHUB_TOKEN"] or "",
        timeout_seconds=timeout_seconds,
    )

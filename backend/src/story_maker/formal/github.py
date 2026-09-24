"""`VerificadorFormal` en modo `github` (ADR 0004): el workflow `LEAN_WORKFLOW` compila el fichero.

Protocolo: se lanza el workflow por `workflow_dispatch` con el fichero en gzip y base64 como input
y `return_run_details: true`, que devuelve el id de la ejecución; se sondea hasta que termina y se
lee el resultado del artefacto `resultado-cronologia`. El artefacto trae la salida de la
compilación, que se interpreta igual que en el modo local (007-I9).
"""

from __future__ import annotations

import asyncio
import base64
import gzip
import io
import json
import time
import zipfile
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import httpx

from story_maker.formal.lean_output import LeanOutput, interpret
from story_maker.formal.result import VerificationOutcome

API = "https://api.github.com"
API_VERSION = "2022-11-28"
INPUT = "fichero"
ARTIFACT = "resultado-cronologia"
RESULT_FILE = "resultado.json"
# La biblioteca Lean y el workflow viven en V2.
REF = "V2"


def encode_input(source: str) -> str:
    """El fichero en gzip (sin fecha en la cabecera: mismo fichero, mismo input) y en base64."""
    return base64.b64encode(gzip.compress(source.encode("utf-8"), mtime=0)).decode("ascii")


class GithubFormalVerifier:
    def __init__(
        self,
        repository: str,
        workflow: str,
        token: str,
        timeout_seconds: float,
        client: httpx.AsyncClient | None = None,
        poll_seconds: float = 10,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.repository = repository
        self.workflow = workflow
        self._token = token
        self.timeout_seconds = timeout_seconds
        self._client = client
        self.poll_seconds = poll_seconds
        self._clock = clock
        self._sleep = sleep

    def __repr__(self) -> str:
        return f"GithubFormalVerifier({self.repository!r}, {self.workflow!r})"

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
            "X-GitHub-Api-Version": API_VERSION,
        }

    @asynccontextmanager
    async def _session(self) -> AsyncIterator[httpx.AsyncClient]:
        if self._client is not None:
            yield self._client
            return
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            yield client

    async def verify(self, source: str) -> VerificationOutcome:
        inputs = {INPUT: encode_input(source)}
        async with self._session() as client:
            return await self._verify(client, inputs)

    async def _verify(
        self, client: httpx.AsyncClient, inputs: dict[str, str]
    ) -> VerificationOutcome:
        repo = f"{API}/repos/{self.repository}"
        launch = await client.post(
            f"{repo}/actions/workflows/{self.workflow}/dispatches",
            headers=self._headers(),
            json={"ref": REF, "inputs": inputs, "return_run_details": True},
        )
        run_id = launch.json()["workflow_run_id"]
        while True:
            run = await client.get(f"{repo}/actions/runs/{run_id}", headers=self._headers())
            if run.json()["status"] == "completed":
                break
            await self._sleep(self.poll_seconds)
        listing = await client.get(
            f"{repo}/actions/runs/{run_id}/artifacts", headers=self._headers()
        )
        artifact_id = next(a["id"] for a in listing.json()["artifacts"] if a["name"] == ARTIFACT)
        download = await client.get(
            f"{repo}/actions/artifacts/{artifact_id}/zip", headers=self._headers()
        )
        with zipfile.ZipFile(io.BytesIO(download.content)) as archive:
            payload = json.loads(archive.read(RESULT_FILE))
        return interpret(LeanOutput(payload["exit_code"], payload["output"]))

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
from typing import Any

import httpx

from story_maker.formal.lean_output import LeanOutput, interpret
from story_maker.formal.result import ChronologyResult, VerificationOutcome, VerifierInterruption

API = "https://api.github.com"
API_VERSION = "2022-11-28"
INPUT = "fichero"
MAX_INPUTS_CHARS = 65_535
DOES_NOT_FIT = "el fichero no cabe en los inputs del workflow"
ARTIFACT = "resultado-cronologia"
RESULT_FILE = "resultado.json"
# La biblioteca Lean y el workflow viven en V2.
REF = "V2"


class Unreachable(Exception):
    """La verificación no llegó a darse; el mensaje nunca lleva el token."""


def read_result(content: bytes) -> LeanOutput:
    """La salida de la compilación desde el zip del artefacto, si cumple el schema del resultado:
    un objeto con `exit_code` (entero) y `output` (texto), sin más claves."""
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            payload = json.loads(archive.read(RESULT_FILE))
    except (zipfile.BadZipFile, KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Unreachable(f"artefacto ilegible ({type(exc).__name__})") from None
    valid = (
        isinstance(payload, dict)
        and set(payload) == {"exit_code", "output"}
        and isinstance(payload["exit_code"], int)
        and not isinstance(payload["exit_code"], bool)
        and isinstance(payload["output"], str)
    )
    if not valid:
        raise Unreachable("el artefacto no cumple el schema del resultado")
    return LeanOutput(payload["exit_code"], payload["output"])


def inputs_fit(inputs: dict[str, str]) -> bool:
    """Los inputs de un `workflow_dispatch` admiten 65.535 caracteres en total (ADR 0004)."""
    return sum(len(value) for value in inputs.values()) <= MAX_INPUTS_CHARS


def _field(response: httpx.Response, key: str, step: str) -> Any:
    try:
        data = response.json()
    except ValueError:
        raise Unreachable(f"respuesta sin JSON en {step}") from None
    if not isinstance(data, dict) or key not in data:
        raise Unreachable(f"respuesta sin {key} en {step}")
    return data[key]


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
        if not inputs_fit(inputs):
            return ChronologyResult("error", reason=DOES_NOT_FIT)
        async with self._session() as client:
            try:
                return await self._verify(client, inputs)
            except Unreachable as exc:
                return VerifierInterruption("verifier_unreachable", str(exc))

    async def _call(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        step: str,
        body: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Una sola petición, sin reintentos: cualquier fallo es `verifier_unreachable`, que ya es
        reanudable. Los mensajes nombran el paso y el código, nunca las cabeceras."""
        try:
            response = await client.request(method, url, headers=self._headers(), json=body)
        except httpx.HTTPError as exc:
            raise Unreachable(f"GitHub no responde en {step} ({type(exc).__name__})") from None
        if not response.is_success:
            raise Unreachable(f"GitHub respondió {response.status_code} en {step}")
        return response

    async def _verify(
        self, client: httpx.AsyncClient, inputs: dict[str, str]
    ) -> VerificationOutcome:
        repo = f"{API}/repos/{self.repository}"
        started = self._clock()
        launch = await self._call(
            client,
            "POST",
            f"{repo}/actions/workflows/{self.workflow}/dispatches",
            "el lanzamiento",
            body={"ref": REF, "inputs": inputs, "return_run_details": True},
        )
        run_id = _field(launch, "workflow_run_id", "el lanzamiento")
        while True:
            run = await self._call(client, "GET", f"{repo}/actions/runs/{run_id}", "el sondeo")
            if _field(run, "status", "el sondeo") == "completed":
                break
            if self._clock() - started >= self.timeout_seconds:
                return VerifierInterruption(
                    "verifier_timeout",
                    f"la ejecución {run_id} sigue sin terminar tras {self.timeout_seconds} s",
                )
            await self._sleep(self.poll_seconds)
        listing = await self._call(
            client, "GET", f"{repo}/actions/runs/{run_id}/artifacts", "la lista de artefactos"
        )
        artifacts = _field(listing, "artifacts", "la lista de artefactos")
        ids = [a.get("id") for a in artifacts if isinstance(a, dict) and a.get("name") == ARTIFACT]
        if not ids:
            raise Unreachable("la ejecución terminó sin artefacto de resultado")
        download = await self._call(
            client, "GET", f"{repo}/actions/artifacts/{ids[0]}/zip", "la descarga del artefacto"
        )
        return interpret(read_result(download.content))

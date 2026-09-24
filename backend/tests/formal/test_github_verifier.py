"""Modo github del `VerificadorFormal` contra un doble HTTP de la API de GitHub (007-C14 a
007-C18, 007-I8). Ninguna prueba sale a la red: el doble es un `httpx.MockTransport`."""

from __future__ import annotations

import base64
import gzip
import io
import json
import zipfile
from collections.abc import Iterator
from typing import Any

import httpx
import pytest

from story_maker.formal.github import GithubFormalVerifier
from story_maker.formal.result import ChronologyResult, VerifierInterruption

REPOSITORY = "cliente/story-maker"
WORKFLOW = "verificar-cronologia.yml"
TOKEN = "TU_CLAVE_AQUI"
RUN_ID, ARTIFACT_ID = 4242, 99
SOURCE = "import Chronology\n\n-- fichero de prueba ⟨1, 2⟩\n"
PASSED_OUTPUT = {
    "exit_code": 0,
    "output": "CRONOLOGIA-LEAN "
    + json.dumps({f"T{n}": {"cumple": True} for n in range(1, 6)})
    + "\n"
    + "\n".join(f"'cumpleT{n}' depends on axioms: [propext]" for n in range(1, 6))
    + "\n",
}


def artifact_zip(payload: Any) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("resultado.json", json.dumps(payload))
    return buffer.getvalue()


class FakeGithub:
    """Doble de la API: lanzamiento, sondeos de la ejecución, lista y descarga del artefacto."""

    def __init__(
        self,
        statuses: tuple[str, ...] = ("queued", "in_progress", "completed"),
        artifact: bytes | None = None,
        failures: dict[str, int | type[Exception]] | None = None,
        listed: bool = True,
    ) -> None:
        self.statuses: Iterator[str] = iter(statuses)
        self.last_status = statuses[-1]
        self.artifact = artifact_zip(PASSED_OUTPUT) if artifact is None else artifact
        self.failures = failures or {}
        self.listed = listed
        self.requests: list[httpx.Request] = []

    def _endpoint(self, request: httpx.Request) -> str:
        path = request.url.path
        if request.url.host != "api.github.com":
            return "blob"
        if request.method == "POST" and path.endswith("/dispatches"):
            return "dispatch"
        if path.endswith(f"/runs/{RUN_ID}/artifacts"):
            return "artifacts"
        if path.endswith(f"/runs/{RUN_ID}"):
            return "run"
        if path.endswith(f"/artifacts/{ARTIFACT_ID}/zip"):
            return "download"
        return "unknown"

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        endpoint = self._endpoint(request)
        failure = self.failures.get(endpoint)
        if isinstance(failure, type):
            raise failure("fallo simulado", request=request)
        if isinstance(failure, int):
            return httpx.Response(failure, json={"message": "fallo simulado"})
        if endpoint == "dispatch":
            return httpx.Response(
                200,
                json={
                    "workflow_run_id": RUN_ID,
                    "run_url": f"https://api.github.com/repos/{REPOSITORY}/actions/runs/{RUN_ID}",
                    "html_url": f"https://github.com/{REPOSITORY}/actions/runs/{RUN_ID}",
                },
            )
        if endpoint == "run":
            status = next(self.statuses, self.last_status)
            conclusion = "success" if status == "completed" else None
            return httpx.Response(
                200, json={"id": RUN_ID, "status": status, "conclusion": conclusion}
            )
        if endpoint == "artifacts":
            listed = [{"id": ARTIFACT_ID, "name": "resultado-cronologia"}] if self.listed else []
            return httpx.Response(200, json={"total_count": len(listed), "artifacts": listed})
        if endpoint == "download":
            return httpx.Response(302, headers={"Location": "https://blob.example.net/a.zip"})
        if endpoint == "blob":
            return httpx.Response(200, content=self.artifact)
        return httpx.Response(404, json={"message": "Not Found"})

    def endpoints(self) -> list[str]:
        return [self._endpoint(r) for r in self.requests]


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.now += seconds


def make_verifier(github: FakeGithub, clock: FakeClock, timeout: float = 900) -> Any:
    client = httpx.AsyncClient(transport=httpx.MockTransport(github.handler), follow_redirects=True)
    return GithubFormalVerifier(
        repository=REPOSITORY,
        workflow=WORKFLOW,
        token=TOKEN,
        timeout_seconds=timeout,
        client=client,
        poll_seconds=10,
        clock=clock,
        sleep=clock.sleep,
    )


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


# --- 007-C14 ---------------------------------------------------------------------------------


async def test_the_github_mode_sends_the_compressed_file_by_workflow_dispatch(
    clock: FakeClock,
) -> None:
    github = FakeGithub()

    result = await make_verifier(github, clock).verify(SOURCE)

    assert isinstance(result, ChronologyResult)
    assert result.result == "passed"
    launches = [r for r in github.requests if github._endpoint(r) == "dispatch"]
    assert len(launches) == 1
    launch = launches[0]
    assert launch.url == (
        f"https://api.github.com/repos/{REPOSITORY}/actions/workflows/{WORKFLOW}/dispatches"
    )
    body = json.loads(launch.content)
    assert body["return_run_details"] is True
    assert set(body["inputs"]) == {"fichero"}
    assert gzip.decompress(base64.b64decode(body["inputs"]["fichero"], validate=True)) == (
        SOURCE.encode("utf-8")
    )
    for request in github.requests:
        if request.url.host == "api.github.com":
            assert request.headers["X-GitHub-Api-Version"] == "2022-11-28"
            assert request.headers["Authorization"] == f"Bearer {TOKEN}"
        else:  # la descarga redirigida al almacén de artefactos no se lleva el token
            assert "Authorization" not in request.headers


# --- 007-C15 ---------------------------------------------------------------------------------


async def test_the_github_mode_polls_the_run_and_reads_the_result_from_the_artifact(
    clock: FakeClock, lean_row: Any
) -> None:
    output = {"exit_code": lean_row.output.exit_code, "output": lean_row.output.output}
    github = FakeGithub(
        statuses=("queued", "in_progress", "in_progress", "in_progress", "completed"),
        artifact=artifact_zip(output),
    )

    result = await make_verifier(github, clock).verify(SOURCE)

    assert isinstance(result, ChronologyResult)
    lean_row.check(result)
    assert github.endpoints() == [
        "dispatch",
        *["run"] * 5,
        "artifacts",
        "download",
        "blob",
    ]
    assert clock.now == 1000.0 + 4 * 10


def zip_with(name: str, content: bytes) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(name, content)
    return buffer.getvalue()


@pytest.mark.parametrize(
    ("label", "github"),
    [
        ("sin artefacto", FakeGithub(listed=False)),
        ("no es un zip", FakeGithub(artifact=b"esto no es un zip")),
        ("zip sin resultado", FakeGithub(artifact=zip_with("otro.json", b"{}"))),
        ("resultado sin JSON", FakeGithub(artifact=zip_with("resultado.json", b"no json"))),
        ("falta la salida", FakeGithub(artifact=artifact_zip({"exit_code": 0}))),
        (
            "salida que no es texto",
            FakeGithub(artifact=artifact_zip({"exit_code": 0, "output": 7})),
        ),
        (
            "código que no es entero",
            FakeGithub(artifact=artifact_zip({"exit_code": "0", "output": ""})),
        ),
        ("claves de más", FakeGithub(artifact=artifact_zip({**PASSED_OUTPUT, "passed": True}))),
        ("no es un objeto", FakeGithub(artifact=artifact_zip([0, ""]))),
    ],
)
async def test_a_finished_run_without_a_valid_result_artifact_gives_no_verdict(
    clock: FakeClock, label: str, github: FakeGithub
) -> None:
    result = await make_verifier(github, clock).verify(SOURCE)

    assert isinstance(result, VerifierInterruption), label
    assert result.reason == "verifier_unreachable"

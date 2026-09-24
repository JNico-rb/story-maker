"""Modo github del `VerificadorFormal` contra un doble HTTP de la API de GitHub (007-C14 a
007-C18, 007-I8). Ninguna prueba sale a la red: el doble es un `httpx.MockTransport`."""

from __future__ import annotations

import base64
import functools
import gzip
import io
import json
import logging
import random
import string
import zipfile
from collections.abc import Iterator
from typing import Any

import httpx
import pytest

from story_maker.formal.github import GithubFormalVerifier, encode_input, inputs_fit
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


# --- 007-C16 ---------------------------------------------------------------------------------


@functools.cache
def source_encoding_to(chars: int) -> str:
    """Un fichero cuyo input codificado mide exactamente `chars` caracteres (múltiplo de 4:
    base64 con relleno). Texto al azar con semilla fija, que gzip apenas comprime."""
    rng = random.Random(7)  # noqa: S311 — datos de prueba deterministas, no criptografía
    text = "".join(rng.choices(string.ascii_letters + string.digits, k=4 * chars))
    low, high = 0, len(text)
    while low < high:  # el prefijo más corto cuyo input llega a `chars`
        middle = (low + high) // 2
        if len(encode_input(text[:middle])) < chars:
            low = middle + 1
        else:
            high = middle
    assert len(encode_input(text[:low])) == chars
    return text[:low]


@pytest.mark.parametrize(
    ("sizes", "fits"),
    [((65_535,), True), ((65_536,), False), ((65_000, 535), True), ((65_000, 536), False)],
)
def test_the_inputs_fit_while_their_encoded_sizes_add_up_to_65535(
    sizes: tuple[int, ...], fits: bool
) -> None:
    inputs = {f"input{i}": "A" * size for i, size in enumerate(sizes)}

    assert inputs_fit(inputs) is fits


async def test_the_largest_file_that_fits_is_sent(clock: FakeClock) -> None:
    github = FakeGithub()

    result = await make_verifier(github, clock).verify(source_encoding_to(65_532))

    assert isinstance(result, ChronologyResult)
    assert github.endpoints()[0] == "dispatch"
    assert len(json.loads(github.requests[0].content)["inputs"]["fichero"]) == 65_532


async def test_a_file_whose_input_does_not_fit_is_not_sent_and_is_an_error(
    clock: FakeClock,
) -> None:
    github = FakeGithub()

    result = await make_verifier(github, clock).verify(source_encoding_to(65_536))

    assert result == ChronologyResult(
        "error", reason="el fichero no cabe en los inputs del workflow"
    )
    assert github.requests == []


# --- 007-C17 ---------------------------------------------------------------------------------

LAUNCH_FAILURES: list[int | type[Exception]] = [
    httpx.ConnectError,
    httpx.ReadTimeout,
    500,
    503,
    401,
    403,
    404,
]


@pytest.fixture
def all_logs(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    caplog.set_level(logging.DEBUG)
    return caplog


def assert_no_token(*things: object, logs: str = "") -> None:
    for thing in things:
        assert TOKEN not in repr(thing)
    assert TOKEN not in logs


@pytest.mark.parametrize("failure", LAUNCH_FAILURES, ids=str)
async def test_a_failed_launch_gives_unreachable_after_a_single_request(
    clock: FakeClock, failure: int | type[Exception], all_logs: pytest.LogCaptureFixture
) -> None:
    github = FakeGithub(failures={"dispatch": failure})

    result = await make_verifier(github, clock).verify(SOURCE)

    assert isinstance(result, VerifierInterruption)
    assert result.reason == "verifier_unreachable"
    assert github.endpoints() == ["dispatch"]
    assert_no_token(result, logs=all_logs.text)


@pytest.mark.parametrize("endpoint", ["run", "artifacts", "download", "blob"])
@pytest.mark.parametrize("failure", [httpx.ConnectError, 500, 502], ids=str)
async def test_a_failed_poll_or_download_gives_unreachable_without_retrying(
    clock: FakeClock,
    endpoint: str,
    failure: int | type[Exception],
    all_logs: pytest.LogCaptureFixture,
) -> None:
    github = FakeGithub(failures={endpoint: failure})

    result = await make_verifier(github, clock).verify(SOURCE)

    assert isinstance(result, VerifierInterruption)
    assert result.reason == "verifier_unreachable"
    assert github.endpoints().count(endpoint) == 1
    assert github.endpoints()[-1] == endpoint
    assert_no_token(result, logs=all_logs.text)


async def test_a_launch_without_run_details_gives_unreachable(clock: FakeClock) -> None:
    github = FakeGithub(failures={"dispatch": 204})

    result = await make_verifier(github, clock).verify(SOURCE)

    assert isinstance(result, VerifierInterruption)
    assert result.reason == "verifier_unreachable"


async def test_a_run_still_unfinished_when_the_timeout_passes_gives_verifier_timeout(
    clock: FakeClock, all_logs: pytest.LogCaptureFixture
) -> None:
    github = FakeGithub(statuses=("in_progress",))

    result = await make_verifier(github, clock, timeout=900).verify(SOURCE)

    assert isinstance(result, VerifierInterruption)
    assert result.reason == "verifier_timeout"
    assert 900 <= clock.now - 1000.0 < 900 + 10
    assert "artifacts" not in github.endpoints()
    assert_no_token(result, logs=all_logs.text)

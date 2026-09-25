"""015-C15: un cambio pedido y confirmado por MCP publica versión y PDF nuevos, y conserva la
anterior. Sobre P (`novela_p`, v1 Toby / v2 Nala): se pide y confirma por MCP que el perro se
llame Luna, el worker corre la ejecución con los dobles de 014 (lean, revisor visual y PDF) y el
writer/editor de la fake del puerto de agente, y las cuatro lecturas MCP reflejan v3 sin tocar
v1 ni v2 (`verification.md` §5, fila 2.10)."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from tests.api.change_requests.conftest import propose, rename
from tests.pipeline.changes.conftest import real_cards, script_judge
from tests.pipeline.conftest import (
    FixedWindows,
    PhaseDouble,
    chapter_call,
    editor_script,
    review,
    writer_script,
)
from tests.pipeline.gate.conftest import GateKit, make_kit
from tests.render.novela_fixture import Novela

from story_maker.agents.fake import FakeAgent
from story_maker.agents.port import AgentPort
from story_maker.api.auth import Clock
from story_maker.config import Config
from story_maker.observability.null import NullObservability
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import Production, Prompts
from story_maker.pipeline.worker import Worker
from story_maker.store.models import Fact, Run

# --- Fixtures propias: el worker con el gate real y sus dobles (014), sobre los mismos dobles
# (session_factory, fake, config, workspace) que ya monta la app MCP -----------------------------


@pytest.fixture
def production(
    agent_port: AgentPort,
    session_factory: sessionmaker[Session],
    telemetry: NullObservability,
    config: Config,
    clock: Clock,
) -> Production:
    return Production(
        port=agent_port,
        session_factory=session_factory,
        telemetry=telemetry,
        config=config,
        windows=FixedWindows(),
        cards=real_cards,
        clock=clock,
        prompts=Prompts(writer="Prompt del writer", editor="Prompt del editor"),
    )


@pytest.fixture
def kit(production: Production, session_factory: sessionmaker[Session], tmp_path: Path) -> GateKit:
    return make_kit(production, session_factory, tmp_path)


@pytest.fixture
def orchestrator(production: Production, kit: GateKit) -> Orchestrator:
    return Orchestrator(production=production, planning=PhaseDouble(), gate=kit.gate)


@pytest.fixture
def worker(
    session_factory: sessionmaker[Session],
    orchestrator: Orchestrator,
    config: Config,
    clock: Clock,
) -> Worker:
    return Worker(
        session_factory, orchestrator.execute, max_resumes=config.max_resumes, clock=clock
    )


def _revise(fake: FakeAgent, chapter: int) -> None:
    fake.script("writer", "revise", writer_script(chapter_call(title=f"Revisado {chapter}")))
    fake.script("editor", None, editor_script(review()))


async def test_a_change_confirmed_by_mcp_publishes_a_new_version_and_pdf_and_keeps_the_previous(
    client: TestClient,
    novela_p: Novela,
    novela_p_headers: dict[str, str],
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    mcp_session,
    worker: Worker,
    kit: GateKit,
) -> None:
    with session_factory() as session:
        nala = (
            session.query(Fact)
            .filter_by(version_id=novela_p.v2_id, attribute="name", value="Nala")
            .one()
        )
        nala_fact_id = nala.id

    async def pdf_bytes(version: int) -> bytes:
        async with mcp_session(novela_p_headers) as mcp:
            result = await mcp.call_tool(
                "download_novel", {"novel_id": novela_p.novel_id, "version": version}
            )
        (content,) = result.content
        return base64.b64decode(content.resource.blob)

    v1_before = await pdf_bytes(1)
    v2_before = await pdf_bytes(2)

    propose(fake, rename(nala_fact_id, "Luna"))
    async with mcp_session(novela_p_headers) as mcp:
        proposal = (
            await mcp.call_tool(
                "request_change",
                {
                    "novel_id": novela_p.novel_id,
                    "selection": {"type": "fact", "fact_id": nala_fact_id},
                    "request": "el perro se llama Luna",
                },
            )
        ).structured_content

    async with mcp_session(novela_p_headers) as mcp:
        confirmation = (
            await mcp.call_tool(
                "confirm_change", {"request_id": proposal["id"], "code": proposal["code"]}
            )
        ).structured_content

    affected = sorted(proposal["affected_chapters"])
    assert affected
    for chapter in affected:
        _revise(fake, chapter)
    script_judge(fake)
    Path(kit.pdf.path).write_bytes(b"%PDF-1.4 candidata de v3, distinta de v1 y v2")

    run_id = await worker.run_next()

    assert run_id == confirmation["run_id"]
    with session_factory() as session:
        run = session.get(Run, confirmation["run_id"])
        assert run is not None
        assert run.status == "published"

    async with mcp_session(novela_p_headers) as mcp:
        versions = (
            await mcp.call_tool("list_versions", {"novel_id": novela_p.novel_id})
        ).structured_content["versions"]
    assert [v["number"] for v in versions] == [1, 2, 3]
    by_number = {v["number"]: v for v in versions}
    assert by_number[3]["changed_chapters"] == affected

    async def chapter_text(version: int, number: int) -> str:
        async with mcp_session(novela_p_headers) as mcp:
            result = await mcp.call_tool(
                "get_chapter",
                {"novel_id": novela_p.novel_id, "version": version, "chapter": number},
            )
        return str(result.structured_content["text"])

    for chapter in affected:
        assert await chapter_text(3, chapter) != await chapter_text(2, chapter)
    untouched = next(n for n in range(1, 11) if n not in affected)
    assert await chapter_text(3, untouched) == await chapter_text(2, untouched)

    async def dog_name(version: int) -> str:
        async with mcp_session(novela_p_headers) as mcp:
            result = await mcp.call_tool(
                "query_story_bible", {"novel_id": novela_p.novel_id, "version": version}
            )
        facts = result.structured_content["story_bible"]["facts"]
        (dog,) = [f for f in facts if f["attribute"] == "name" and f["value"] in ("Nala", "Luna")]
        return str(dog["value"])

    assert await dog_name(3) == "Luna"
    assert await dog_name(2) == "Nala"

    v3_after = await pdf_bytes(3)
    v2_after = await pdf_bytes(2)
    v1_after = await pdf_bytes(1)
    assert v3_after != v2_after
    assert v2_after == v2_before
    assert v1_after == v1_before

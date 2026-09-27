"""Invariantes del gate: 012-I1 (`NuncaPublicaSinValidar`)."""

from __future__ import annotations

import asyncio
import contextlib
import dataclasses
from dataclasses import dataclass, field

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    Seed,
    chapter_call,
    editor_script,
    review,
    text_of,
    writer_script,
)
from tests.pipeline.gate.conftest import (
    GateKit,
    PdfDouble,
    append_to_chapter,
    chapter_hashes,
    evaluation,
    gate_passes,
    results_of_pass,
    script_judges,
    visual_defects,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Trace
from story_maker.pipeline.gate.phase import PdfOutcome
from story_maker.pipeline.runs import RunStop
from story_maker.store.models import BannedTerm, Version

ALL_VALIDATORS = {
    "elementos-obligatorios",
    "nombres-exactos",
    "palabras-prohibidas",
    "cronologia-lean",
    "juez-novela",
    "pdf-enlaces",
}


@dataclass
class SnapshotPdf(PdfDouble):
    """El doble del PDF, que guarda la huella de la candidata cuando la etapa 4 la renderiza."""

    session_factory: sessionmaker[Session] | None = None
    snapshots: list[dict[int, str]] = field(default_factory=list)

    async def __call__(self, version_id: int) -> PdfOutcome:
        assert self.session_factory is not None
        self.snapshots.append(chapter_hashes(self.session_factory, version_id))
        return await super().__call__(version_id)


def _rewrite(fake: FakeAgent, *, banned: bool) -> None:
    text = f"{text_of(1249)} tormentas" if banned else None
    fake.script("writer", "rewrite", writer_script(chapter_call(title="Reescrito", text=text)))
    fake.script("editor", None, editor_script(review()))


def _script(
    session_factory: sessionmaker[Session],
    seed: Seed,
    fake: FakeAgent,
    kit: GateKit,
    stage: int,
    failing: int,
) -> None:
    """Las pasadas 1..`failing` no superan la etapa `stage`; la siguiente, si la hay, sí."""
    if stage == 1:
        with session_factory() as session:
            session.add(
                BannedTerm(
                    level="user",
                    user_id=seed.user_id,
                    term="tormenta",
                    type="word",
                    normalized="tormenta",
                )
            )
            session.commit()
        append_to_chapter(session_factory, seed.version_id, 4, "Hubo tormentas.")
    passes = min(failing + 1, 3)
    for number in range(1, passes + 1):
        fails = number <= failing
        # Sin ciclos (la pasada 3), un defecto atribuible ya no falla: la pasada sigue hasta
        # publicar (cambio de producto de 2026-09-26), así que también hace falta un juez ahí.
        if not fails or stage >= 2 or number == 3:
            low = fails and stage == 2
            judged = evaluation({"continuidad": 2}, {"continuidad": (4,)}) if low else evaluation()
            script_judges(fake, judged)
        if fails and stage == 3:
            kit.visual.outcomes.append(visual_defects(4))
        if fails and stage == 4:
            kit.pdf.outcomes.append(PdfOutcome(None, detail="sin PDF"))
        if fails and number < 3:
            _rewrite(fake, banned=stage == 1 and number < failing)


CASES = [(stage, failing) for stage in (1, 2, 3) for failing in (1, 2, 3)] + [(4, 1)]


@pytest.mark.parametrize(("stage", "failing"), CASES)
def test_the_version_publishes_unless_its_last_pass_hits_a_render_failure(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
    stage: int,
    failing: int,
) -> None:
    """Cambio de producto (2026-09-26): agotados los ciclos, un defecto atribuible en las etapas 1
    a 3 ya no falla — la pasada sigue y publica con él. Solo la etapa 4 (`render_failure`, no
    atribuible) sigue bloqueando siempre la publicación, con o sin ciclos."""
    pdf = SnapshotPdf(kit.log, kit.pdf.path, session_factory=session_factory)
    kit.pdf = pdf
    gate = dataclasses.replace(kit.gate, pdf=pdf)
    _script(session_factory, at_gate, fake, kit, stage, failing)

    with contextlib.suppress(RunStop):
        asyncio.run(gate(at_gate.run_id, trace))

    with session_factory() as session:
        version = session.get_one(Version, at_gate.version_id)
        status = version.status
    passes = gate_passes(session_factory, at_gate.run_id)
    published = stage != 4
    assert (status == "published") is published
    if not published:
        assert passes[-1][1] == "fail"
        return
    last, outcome = passes[-1]
    assert (last, outcome) == (min(failing + 1, 3), "accept")
    last_results = results_of_pass(session_factory, at_gate.run_id, last)
    assert {r.validator for r in last_results} == ALL_VALIDATORS
    if failing < 3:
        # Una pasada que de verdad limpió las cuatro etapas: todo pasó.
        assert all(r.passed for r in last_results)
    else:
        # Los ciclos se agotaron con el defecto de la etapa `stage` sin corregir: la pasada
        # publica de todos modos, pero ese validador sigue en falso (la etapa 3, `revision-visual`,
        # no deja fila en este doble simplificado, así que ahí no hay nada que quede en falso).
        failing_validator = {1: "palabras-prohibidas", 2: "juez-novela"}.get(stage)
        not_passed = {r.validator for r in last_results if not r.passed}
        assert not_passed == ({failing_validator} if failing_validator else set())
    assert pdf.snapshots[-1] == chapter_hashes(session_factory, at_gate.version_id)

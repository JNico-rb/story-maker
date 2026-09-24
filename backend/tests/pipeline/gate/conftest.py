"""Fixtures del gate de publicación (012): la candidata de `tests/pipeline/conftest.py` con su
mundo y sus 10 capítulos aceptados, la ejecución en fase `gate`, y dobles del verificador formal
(el de 007, programado), de la etapa 3 y del PDF. El juez, el writer y el editor corren en el
doble falso del puerto de agente; la telemetría, en el doble nulo.

Fixture común: umbrales en 3, `max_retries.chapter` = 2 y `max_retries.gate_cycles` = 2."""

from __future__ import annotations

import dataclasses
import datetime as dt
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    NOW,
    USAGE,
    Seed,
    chapter_call,
    editor_script,
    review,
    text_of,
    writer_script,
)

from story_maker.agents.fake import Call, FakeAgent, Say, Script, Step
from story_maker.config import Config
from story_maker.formal.candidate import CandidateVerification, verify_candidate
from story_maker.formal.defects import Defect
from story_maker.formal.double import ProgrammedFormalVerifier
from story_maker.formal.result import (
    INVARIANTS,
    ChronologyResult,
    VerificationOutcome,
)
from story_maker.observability.port import Trace
from story_maker.pipeline.acceptance import chapter_hash
from story_maker.pipeline.gate.phase import Gate, PdfOutcome, VisualReviewOutcome
from story_maker.pipeline.production import Production
from story_maker.store.models import Chapter, Checkpoint, Run, World

RUBRIC = (
    "continuidad",
    "coherencia-personajes",
    "arco-y-final",
    "ritmo",
    "tono",
    "personalizacion-natural",
    "no-cliche",
)
PASSED = ChronologyResult("passed", dict.fromkeys(INVARIANTS, True))


def evaluation(
    scores: int | dict[str, int] = 4, chapters: dict[str, Sequence[int]] | None = None
) -> dict[str, Any]:
    by_criterion = dict.fromkeys(RUBRIC, scores) if isinstance(scores, int) else scores
    cited = chapters or {}
    return {
        c: {
            "score": by_criterion.get(c, 4),
            "justification": f"justificación de {c}",
            "chapters": list(cited.get(c, (1,))),
        }
        for c in RUBRIC
    }


def judge_script(*evaluations: dict[str, Any], steps: Sequence[Step] = ()) -> Script:
    calls = tuple(Call("submit_evaluation", e) for e in evaluations)
    return Script(steps=(*steps, *calls, Say("Fin.")), usage=USAGE, sdk_cost_usd=0.4)


@dataclass
class OrderLog:
    """El orden en que corren las etapas con doble (Lean, etapa 3, PDF)."""

    entries: list[str] = field(default_factory=list)


@dataclass
class LeanDouble:
    """La verificación real de 007 (`verify_candidate`) con el verificador programado."""

    session_factory: sessionmaker[Session]
    data_dir: Path
    log: OrderLog
    outcomes: list[VerificationOutcome] = field(default_factory=list)
    calls: list[int] = field(default_factory=list)

    async def __call__(self, run_id: int) -> CandidateVerification:
        self.calls.append(run_id)
        self.log.entries.append("cronologia-lean")
        outcome = self.outcomes.pop(0) if self.outcomes else PASSED
        return await verify_candidate(
            self.session_factory,
            ProgrammedFormalVerifier([outcome]),
            run_id=run_id,
            data_dir=self.data_dir,
            now=NOW,
        )


@dataclass
class VisualDouble:
    log: OrderLog
    outcomes: list[VisualReviewOutcome] = field(default_factory=list)
    calls: list[int] = field(default_factory=list)

    async def __call__(self, run_id: int, trace: Trace) -> VisualReviewOutcome:
        self.calls.append(run_id)
        self.log.entries.append("revision-visual")
        return self.outcomes.pop(0) if self.outcomes else VisualReviewOutcome()


@dataclass
class PdfDouble:
    log: OrderLog
    path: str
    outcomes: list[PdfOutcome] = field(default_factory=list)
    calls: list[int] = field(default_factory=list)

    async def __call__(self, version_id: int) -> PdfOutcome:
        self.calls.append(version_id)
        self.log.entries.append("pdf")
        return self.outcomes.pop(0) if self.outcomes else PdfOutcome(self.path, True)


@dataclass
class GateKit:
    gate: Gate
    lean: LeanDouble
    visual: VisualDouble
    pdf: PdfDouble
    log: OrderLog


@pytest.fixture
def config(config: Config) -> Config:
    return dataclasses.replace(config, max_retries={**config.max_retries, "gate_cycles": 2})


def seed_world(session: Session, version_id: int) -> None:
    session.add(
        World(
            version_id=version_id,
            novum_description="las máquinas aprendieron a soñar",
            novum_scope="technological",
            novum_date=dt.date(2030, 1, 1),
            consequences=[],
        )
    )


def seed_chapters(
    session: Session, version_id: int, texts: dict[int, str] | None = None
) -> None:
    for number in range(1, 11):
        text = (texts or {}).get(number, text_of(1250))
        title = f"Capítulo {number}"
        session.add(
            Chapter(
                version_id=version_id,
                number=number,
                title=title,
                text=text,
                summary=f"Resumen {number}",
                word_count=1250,
                content_hash=chapter_hash(title, text),
            )
        )


@pytest.fixture
def at_gate(session_factory: sessionmaker[Session], seed: Seed) -> Seed:
    """La ejecución de la fixture con los 10 capítulos aceptados y la fase en `gate`."""
    with session_factory() as session:
        seed_world(session, seed.version_id)
        seed_chapters(session, seed.version_id)
        for k in range(1, 11):
            session.add(Checkpoint(run_id=seed.run_id, chapter=k, created_at=NOW))
        run = session.get(Run, seed.run_id)
        assert run is not None
        run.phase, run.chapter = "gate", None
        session.commit()
    return seed


def make_kit(
    production: Production, session_factory: sessionmaker[Session], data_dir: Path
) -> GateKit:
    log = OrderLog()
    lean = LeanDouble(session_factory, data_dir, log)
    visual = VisualDouble(log)
    pdf = PdfDouble(log, str(data_dir / "candidata.pdf"))
    gate = Gate(
        production=production,
        lean=lean,
        visual_review=visual,
        pdf=pdf,
        judge_prompt="Prompt del juez",
    )
    return GateKit(gate, lean, visual, pdf, log)


@pytest.fixture
def kit(
    production: Production, session_factory: sessionmaker[Session], tmp_path: Path
) -> GateKit:
    return make_kit(production, session_factory, tmp_path)


def script_rewrites(fake: FakeAgent, count: int) -> None:
    """`count` reescrituras de capítulo que se aceptan al primer intento."""
    for _ in range(count):
        fake.script("writer", "rewrite", writer_script(chapter_call(title="Reescrito")))
        fake.script("editor", None, editor_script(review()))


def script_judges(fake: FakeAgent, *evaluations: dict[str, Any]) -> None:
    for e in evaluations:
        fake.script("judge", None, judge_script(e))


def defects_at(*chapters: int, validator: str = "revision-visual") -> tuple[Defect, ...]:
    return tuple(Defect(validator, None, True, c, f"defecto en {c}") for c in chapters)


def visual_defects(*chapters: int) -> VisualReviewOutcome:
    return VisualReviewOutcome(defects=defects_at(*chapters))


def lean_outcomes(kit: GateKit, outcomes: Iterable[VerificationOutcome]) -> None:
    kit.lean.outcomes.extend(outcomes)

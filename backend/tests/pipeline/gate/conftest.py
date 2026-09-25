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
from typing import Any, cast

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import (
    NOW,
    USAGE,
    Seed,
    chapter_call,
    editor_script,
    review,
    seed_run,
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
from story_maker.pipeline.gate.phase import Gate, GateJob, PdfOutcome, VisualReviewOutcome
from story_maker.pipeline.production import Production
from story_maker.store.models import (
    Attempt,
    ChangeRequest,
    Chapter,
    Checkpoint,
    Fact,
    OutlineChapter,
    Run,
    ValidatorResult,
    Version,
    World,
)
from story_maker.store.session import unit_of_work
from story_maker.store.version_copy import copy_version

RUBRIC = (
    "continuidad",
    "coherencia-personajes",
    "arco-y-final",
    "ritmo",
    "tono",
    "personalizacion-natural",
    "no-cliche",
)
STAGE_1 = {"elementos-obligatorios", "nombres-exactos", "palabras-prohibidas"}
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

    async def __call__(self, job: GateJob, trace: Trace) -> VisualReviewOutcome:
        self.calls.append(job.run_id)
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


def seed_chapters(session: Session, version_id: int, texts: dict[int, str] | None = None) -> None:
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
def kit(production: Production, session_factory: sessionmaker[Session], tmp_path: Path) -> GateKit:
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


def with_gate_cycles(kit: GateKit, cycles: int) -> Gate:
    """El gate del kit con otro `max_retries.gate_cycles`."""
    production = kit.gate.production
    config = dataclasses.replace(
        production.config, max_retries={**production.config.max_retries, "gate_cycles": cycles}
    )
    return dataclasses.replace(kit.gate, production=dataclasses.replace(production, config=config))


def results(session_factory: sessionmaker[Session], run_id: int) -> list[ValidatorResult]:
    """Los resultados de los validadores de novela (sin capítulo) de la ejecución, en orden."""
    with session_factory() as session:
        return list(
            session.query(ValidatorResult)
            .filter(ValidatorResult.run_id == run_id, ValidatorResult.chapter.is_(None))
            .order_by(ValidatorResult.id)
            .all()
        )


def results_of_pass(
    session_factory: sessionmaker[Session], run_id: int, cycle: int
) -> list[ValidatorResult]:
    return [
        r
        for r in results(session_factory, run_id)
        if cast(dict[str, Any], r.detail)["gate_cycle"] == cycle
    ]


def run_of(session_factory: sessionmaker[Session], run_id: int) -> Run:
    with session_factory() as session:
        run = session.get(Run, run_id)
        assert run is not None
        return run


def gate_passes(session_factory: sessionmaker[Session], run_id: int) -> list[tuple[int, str]]:
    """Las pasadas contadas: (número, desenlace)."""
    with session_factory() as session:
        rows = session.query(Attempt).filter(
            Attempt.run_id == run_id, Attempt.evaluable == "gate_cycle"
        )
        return [(a.number, cast(str, a.outcome)) for a in rows.order_by(Attempt.number)]


def append_to_chapter(
    session_factory: sessionmaker[Session], version_id: int, number: int, extra: str
) -> None:
    with session_factory() as session:
        chapter = (
            session.query(Chapter)
            .filter(Chapter.version_id == version_id, Chapter.number == number)
            .one()
        )
        chapter.text = f"{chapter.text} {extra}"
        chapter.content_hash = chapter_hash(chapter.title, chapter.text)
        session.commit()


def chapter_hashes(session_factory: sessionmaker[Session], version_id: int) -> dict[int, str]:
    with session_factory() as session:
        rows = session.query(Chapter).filter(Chapter.version_id == version_id)
        return {c.number: c.content_hash for c in rows}


FAIR = "se perdió en la feria"
FAIR_ELEMENT = 77


def seed_unused_element(
    session_factory: sessionmaker[Session], seed: Seed, chapters: Sequence[int]
) -> int:
    """El recuerdo obligatorio «se perdió en la feria», asignado por el outline a `chapters`, sin
    ningún `UsoDeHecho`; devuelve el id de su hecho."""
    with session_factory() as session:
        fact = Fact(
            version_id=seed.version_id,
            subject_type="character",
            character_id=seed.characters["Marta"],
            attribute="memory",
            value=FAIR,
            origin="brief",
            mandatory=True,
            personal_element_id=FAIR_ELEMENT,
        )
        session.add(fact)
        outline = session.query(OutlineChapter).filter(
            OutlineChapter.version_id == seed.version_id, OutlineChapter.number.in_(chapters)
        )
        for chapter in outline:
            chapter.assigned_elements = [str(FAIR_ELEMENT)]
        session.commit()
        return fact.id


@dataclass(frozen=True)
class Change:
    """La candidata de un cambio sobre la v3 de la novela de la fixture."""

    run_id: int
    base_id: int
    candidate_id: int
    request_id: int


def publish_as(session: Session, version_id: int, number: int) -> None:
    version = session.get_one(Version, version_id)
    version.status, version.number, version.published_at = "published", number, NOW


def seed_change_over_v3(session_factory: sessionmaker[Session], seed: Seed) -> Change:
    """La candidata de la fixture pasa a ser la v3 publicada (con v1 y v2 antes); de ella nace la
    candidata de un cambio con los capítulos 2 y 5 reescritos y su solicitud `confirmed`."""
    with session_factory() as session:
        for number in (1, 2):
            session.add(
                Version(
                    novel_id=seed.novel_id,
                    status="published",
                    number=number,
                    changed_chapters=[],
                    created_at=NOW,
                    published_at=NOW,
                )
            )
        publish_as(session, seed.version_id, 3)
        session.get_one(Run, seed.run_id).status = "published"
        session.commit()
    with unit_of_work(session_factory) as uow:
        candidate_id = copy_version(uow, seed.version_id, now=NOW).version.id
    with session_factory() as session:
        for chapter in session.query(Chapter).filter(
            Chapter.version_id == candidate_id, Chapter.number.in_((2, 5))
        ):
            chapter.text = f"{chapter.text} cambiado"
            chapter.content_hash = chapter_hash(chapter.title, chapter.text)
        run = seed_run(
            session,
            seed.novel_id,
            phase="gate",
            chapter=None,
            candidate=candidate_id,
            checkpoints=(),
        )
        run.type, run.base_version_id = "change_request", seed.version_id
        request = ChangeRequest(
            novel_id=seed.novel_id,
            base_version_id=seed.version_id,
            selection_type="fragment",
            selection={"chapter": 2},
            request="que llueva",
            status="confirmed",
            run_id=run.id,
            created_at=NOW,
        )
        session.add(request)
        session.commit()
        return Change(run.id, seed.version_id, candidate_id, request.id)


def version_of(session_factory: sessionmaker[Session], version_id: int) -> Version:
    with session_factory() as session:
        return session.get_one(Version, version_id)

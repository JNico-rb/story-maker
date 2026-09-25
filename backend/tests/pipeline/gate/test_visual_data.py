"""La comprobación de datos de la ficha, antes de abrir el revisor (017-C10, 017-C11)."""

from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed
from tests.pipeline.gate.visual import (
    add_place,
    chapter_text,
    job_of,
    make_settings,
    make_stage,
    reviewer_sessions,
    seed_visual,
    set_chapter_text,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Trace
from story_maker.pipeline.production import Production

ZAHARA = "Zahara"


def name_in_chapters(
    session_factory: sessionmaker[Session], seed: Seed, name: str, chapters: tuple[int, ...]
) -> None:
    for number in chapters:
        text = f"{chapter_text(number)} Al anochecer llegaron a {name} por el camino viejo."
        set_chapter_text(session_factory, seed.version_id, number, text)


def test_an_entity_without_chapter_named_in_the_text_is_an_attributed_data_failure_no_reviewer(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    trace: Trace,
    tmp_path: Path,
) -> None:
    seed_visual(session_factory, at_gate)
    add_place(session_factory, at_gate.version_id, ZAHARA)
    name_in_chapters(session_factory, at_gate, ZAHARA, (3, 7))

    outcome = asyncio.run(make_stage(production, make_settings(tmp_path))(job_of(at_gate), trace))

    assert reviewer_sessions(fake) == []
    assert outcome.failure is None
    assert outcome.reregister is True
    assert [d.chapter for d in outcome.defects] == [3, 7]
    for defect in outcome.defects:
        assert (defect.validator, defect.criterion, defect.blocking) == (
            "revision-visual",
            "ficha",
            True,
        )
        assert f"«{ZAHARA}»" in defect.message
        assert "la ficha no" in defect.message

"""Ningún capítulo aceptado tiene un defecto bloqueante (011-I6): sobre entregas generadas, todo
lo aceptado tiene de 1.000 a 1.500 palabras, ninguna variante de nombre, ninguna coincidencia
prohibida y una revisión sin bloqueantes."""

from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from tests.pipeline.conftest import (
    BANNED,
    CRITERIA,
    SuccessorCards,
    chapter_call,
    editor_script,
    fresh_database,
    make_production,
    review,
    seed_candidate,
    seed_novel,
    seed_run,
    seed_user,
    text_of,
    writer_script,
)

from story_maker.agents.fake import FakeAgent
from story_maker.config import Config
from story_maker.pipeline.production import ChapterProducer, Production
from story_maker.pipeline.runs import RunStop
from story_maker.store.models import Chapter, Character, ValidatorResult
from story_maker.validators.chapter_length import count_words
from story_maker.validators.exact_names import name_variants

PROPERTY = settings(
    max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)

# Sesgadas hacia lo que se acepta y hacia los límites, para que la propiedad no sea vacía.
rarely = st.sampled_from([False, False, False, True])
delivery = st.fixed_dictionaries(
    {
        "words": st.one_of(st.integers(950, 1050), st.integers(1450, 1550), st.integers(950, 1550)),
        "variant": rarely,
        "banned": rarely,
        "scores": st.fixed_dictionaries({c: st.sampled_from([2, 3, 4, 5, 5]) for c in CRITERIA}),
        "blocking_defect": rarely,
    }
)


def delivered_text(words: int, variant: bool, banned: bool) -> str:
    tokens = text_of(words).split(" ")
    if variant:
        tokens[0] = "Martha"
    if banned:
        tokens[1] = BANNED
    return " ".join(tokens)


@PROPERTY
@given(deliveries=st.lists(delivery, min_size=4, max_size=4))
def test_no_accepted_chapter_has_a_blocking_defect(
    deliveries: list[dict[str, Any]],
    config: Config,
    workspace: Path,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    with fresh_database(tmp_path_factory.mktemp("db")) as session_factory:
        with session_factory() as session:
            user = seed_user(session)
            novel = seed_novel(session, user.id)
            version, *_ = seed_candidate(session, novel.id)
            run = seed_run(session, novel.id, candidate=version.id)
            session.commit()
            run_id, version_id, novel_id = run.id, version.id, novel.id
        fake = FakeAgent()
        for k, d in enumerate(deliveries):
            text = delivered_text(d["words"], d["variant"], d["banned"])
            defects = (
                [{"criterion": "prosa", "blocking": True, "message": "marca bloqueante"}]
                if d["blocking_defect"]
                else []
            )
            fake.script(
                "writer", "write" if k == 0 else "rewrite", writer_script(chapter_call(text=text))
            )
            fake.script("editor", None, editor_script(review(d["scores"], defects=defects)))
        production = make_production(
            session_factory, config, workspace, fake, SuccessorCards(), novel_id
        )

        with contextlib.suppress(RunStop):
            asyncio.run(run_chapter(production, run_id))

        with session_factory() as session:
            chapter = (
                session.query(Chapter).filter_by(version_id=version_id, number=1).one_or_none()
            )
            if chapter is None:
                return
            names = [
                c.canonical_name for c in session.query(Character).filter_by(version_id=version_id)
            ]
            rubric = (
                session.query(ValidatorResult)
                .filter_by(run_id=run_id, validator="rubrica-capitulo", passed=True)
                .one()
            )
        assert 1000 <= count_words(chapter.text) <= 1500
        assert name_variants(chapter.title, chapter.text, names) == []
        assert BANNED not in chapter.text
        assert not any(d["blocking"] for d in rubric.detail["defects"])


async def run_chapter(production: Production, run_id: int) -> None:
    with production.telemetry.trace(f"run:{run_id}", name="generacion") as trace:
        await ChapterProducer(production).produce_chapter(run_id, 1, trace)

"""Escritura de `chronology_files` que usa 007-validador-lean (spec 009, alcance)."""

from __future__ import annotations

from typing import Any

from story_maker.store import models
from story_maker.store.chronology_files import record_chronology_file
from story_maker.store.session import unit_of_work


def test_a_chronology_file_row_keeps_its_hash_result_and_detail(store: Any) -> None:
    novel_id = store.new_novel()
    with unit_of_work(store.session_factory) as uow:
        run = models.Run(
            novel_id=novel_id,
            type="generation",
            status="running",
            resumes=0,
            created_at=store.now,
        )
        uow.add(run)
        uow.session.flush()
        row = record_chronology_file(
            uow,
            run_id=run.id,
            content_hash="a" * 64,
            result="failed",
            detail={"T3": [11, 31, 33]},
            now=store.now,
        )

    with store.session() as session:
        stored = session.get(models.ChronologyFile, row.id)
        assert (stored.run_id, stored.content_hash, stored.result, stored.detail) == (
            run.id,
            "a" * 64,
            "failed",
            {"T3": [11, 31, 33]},
        )
        assert stored.created_at == store.now

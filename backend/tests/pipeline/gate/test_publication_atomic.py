"""012-I3 · La publicación es atómica."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed
from tests.pipeline.gate.conftest import (
    GateKit,
    evaluation,
    gate_passes,
    run_of,
    script_judges,
    seed_change_over_v3,
    version_of,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Trace
from story_maker.pipeline.gate import publication
from story_maker.pipeline.runs import RunStop
from story_maker.store.models import ChangeRequest


def _after(real: Callable[..., Any]) -> Callable[..., Any]:
    """La escritura real, y después un fallo: lo ya escrito en la unidad de trabajo se deshace."""

    def broken(*args: Any, **kwargs: Any) -> Any:
        real(*args, **kwargs)
        raise RuntimeError("disco lleno")

    return broken


@pytest.mark.parametrize("step", ["publish", "record_pass", "mark_applied"])
def test_publication_is_atomic_whatever_write_fails_inside_it(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
    monkeypatch: pytest.MonkeyPatch,
    step: str,
) -> None:
    change = seed_change_over_v3(session_factory, at_gate)
    script_judges(fake, evaluation())
    monkeypatch.setattr(publication, step, _after(getattr(publication, step)))

    with pytest.raises(RunStop):
        asyncio.run(kit.gate(change.run_id, trace))

    version = version_of(session_factory, change.candidate_id)
    assert (version.status, version.number, version.published_at) == ("candidate", None, None)
    assert (version.changed_chapters, version.pdf_path) == ([], None)
    run = run_of(session_factory, change.run_id)
    assert (run.status, run.finished_at) == ("running", None)
    with session_factory() as session:
        assert session.get_one(ChangeRequest, change.request_id).status == "confirmed"
    assert gate_passes(session_factory, change.run_id) == []

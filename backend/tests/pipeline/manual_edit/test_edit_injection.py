"""019-C28 (RT16) · Una inyección en el texto editado que el editor obedece: el texto llega solo
al editor, delimitado y declarado como dato, y el gate rechaza la edición."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed, editor_script
from tests.pipeline.gate.conftest import GateKit, evaluation, judge_script
from tests.pipeline.manual_edit.conftest import N
from tests.pipeline.manual_edit.test_edit_rejected import (
    assert_rejected_and_v1_current,
    chapter_3_review,
    dog_seen_in_chapter_7,
    worker_with_lean,
)
from tests.pipeline.manual_edit.test_edit_run import queue_edit, roles
from tests.pipeline.manual_edit.test_save import INJECTION, lead

from story_maker.agents.fake import FakeAgent
from story_maker.pipeline.orchestrator import Orchestrator
from story_maker.pipeline.production import Production
from story_maker.store.models import AuditLog


async def test_an_injection_the_editor_obeys_reaches_only_the_editor_and_the_gate_rejects_it(
    n: N,
    seed: Seed,
    fake: FakeAgent,
    kit: GateKit,
    production: Production,
    orchestrator: Orchestrator,
    session_factory: sessionmaker[Session],
) -> None:
    dog_seen_in_chapter_7(session_factory, n, seed)
    text = lead(session_factory, n, f"Luego dijo {INJECTION}.")
    run_id = queue_edit(session_factory, n, text)
    obeys = chapter_3_review(session_factory, n, seed, excludes_dog=True)
    fake.script("editor", None, editor_script(obeys))
    fake.script("judge", None, judge_script(evaluation(4)))

    await worker_with_lean(production, orchestrator, kit).run_next()

    assert_rejected_and_v1_current(session_factory, n, run_id)
    assert roles(fake) == [("editor", 3), ("judge", None)]
    editor = fake.sessions[0].request
    inputs = json.loads(editor.message)["call_inputs"]
    assert inputs["text"] == text
    assert "dato" in inputs["manual_edit"]
    assert INJECTION not in editor.prompt
    assert kit.lean.calls == [run_id]
    with session_factory() as session:
        flags = session.query(AuditLog).filter_by(origin="manual_edit", decision="flag")
        assert any(INJECTION in row.detail[0]["phrase"] for row in flags)

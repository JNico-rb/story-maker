"""017-C16 · Cada revisión deja su resultado, su span y sus scores."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, cast

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed
from tests.pipeline.gate.conftest import results
from tests.pipeline.gate.visual import (
    ZAHARA,
    add_place,
    faithful,
    job_of,
    make_settings,
    make_stage,
    name_in_chapters,
    reviewer_script,
    seed_visual,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Span, Trace
from story_maker.pipeline.production import Production

PART_SCORES = ["portada", "indice", "capitulos", "ficha"]


def _no_dedication() -> dict[str, Any]:
    delivery = faithful()
    delivery["portada"]["dedication"] = ""
    return delivery


def _all_spans(spans: list[Span]) -> list[Span]:
    return [s for span in spans for s in (span, *_all_spans(span.children))]


@pytest.mark.parametrize(
    ("case", "passed", "parts", "session"),
    [
        ("C04", True, dict.fromkeys(PART_SCORES, 1), True),
        ("C06", False, {"portada": 0, "indice": 1, "capitulos": 1, "ficha": 1}, True),
        ("C10", False, {"ficha": 0}, False),
    ],
)
def test_each_review_leaves_its_result_its_span_and_its_scores(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    trace: Trace,
    tmp_path: Path,
    case: str,
    passed: bool,
    parts: dict[str, int],
    session: bool,
) -> None:
    seed_visual(session_factory, at_gate)
    if case == "C10":
        add_place(session_factory, at_gate.version_id, ZAHARA)
        name_in_chapters(session_factory, at_gate, ZAHARA, (3, 7))
    else:
        delivery = faithful() if case == "C04" else _no_dedication()
        fake.script("visual_reviewer", None, reviewer_script(delivery))

    stage = make_stage(production, make_settings(tmp_path))
    asyncio.run(stage(job_of(at_gate, cycle=2), trace))

    [row] = [
        r for r in results(session_factory, at_gate.run_id) if r.validator == "revision-visual"
    ]
    assert (row.version_id, row.chapter, row.passed) == (at_gate.version_id, None, passed)
    assert row.score == (1.0 if passed else 0.0)
    detail = cast(dict[str, Any], row.detail)
    assert detail["gate_cycle"] == 2
    assert {p["name"]: p["score"] for p in detail["parts"]} == parts
    for defect in detail["defects"]:
        assert set(defect) >= {"part", "kind", "chapter", "message"}
    if case == "C06":
        [defect] = detail["defects"]
        assert (defect["part"], defect["kind"], defect["chapter"]) == ("portada", "render", None)
    if case == "C10":
        assert [(d["kind"], d["chapter"]) for d in detail["defects"]] == [
            ("datos", 3),
            ("datos", 7),
        ]

    [validator_span] = [s for s in trace.spans if s.name == "validador:revision-visual"]
    scores = {s.name: s for s in trace.scores if s.name.startswith("revision-visual")}
    expected_names = {"revision-visual", *(f"revision-visual/{p}" for p in parts)}
    assert set(scores) == expected_names
    assert scores["revision-visual"].value == (1 if passed else 0)
    for part, value in parts.items():
        assert scores[f"revision-visual/{part}"].value == value
    assert all(s.span is validator_span for s in scores.values())
    if not passed:
        failing = next(p for p, v in parts.items() if v == 0)
        assert scores[f"revision-visual/{failing}"].comment
        assert scores[f"revision-visual/{failing}"].comment != "sin defectos"
    roles = [s.name for s in _all_spans(validator_span.children)]
    assert ("rol:revisor-visual" in roles) is session
    if session:
        [role] = [s for s in validator_span.children if s.name == "rol:revisor-visual"]
        assert "tool:submit_visual_review" in [s.name for s in role.children]

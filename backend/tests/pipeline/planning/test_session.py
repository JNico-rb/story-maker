"""Policy sobre la entrega del plan (010-C09): el hook de policy sobre `submit_plan`, con las
prohibidas reales de 005 y el `AuditLog` real, en vez de los dobles de `tests/agents/`."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.planning.conftest import audit_rows, ban

from story_maker.agents.fake import Call, FakeAgent, Say, Script
from story_maker.agents.port import AgentPort, SessionRequest


def _plan(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "world": {
            "novum_description": "Las IA razonan sobre sus propios límites éticos.",
            "novum_scope": "technological",
            "novum_date": "2021-05-01",
            "consequences": ["Una consecuencia.", "Otra consecuencia."],
        },
        "characters": [{"name": "Nia", "species": "artificial"}],
        "places": [{"name": "el puerto nuevo"}],
        "facts": [],
        "chapters": [
            {
                "number": 1,
                "title": "Capítulo 1",
                "arc_function": "arranque",
                "beats": [{"number": 1, "description": "Marta despierta."}],
            }
        ],
        "style_sheet": {
            "narrator": "third",
            "tense": "past",
            "default_treatment": "tu",
        },
        "title": "El verano de Marta",
    }
    base.update(overrides)
    return base


@pytest.mark.parametrize(
    ("clean_plan", "dirty_plan", "term"),
    [
        (
            _plan(),
            _plan(
                chapters=[
                    {
                        "number": 1,
                        "title": "Capítulo 1",
                        "arc_function": "arranque",
                        "beats": [{"number": 1, "description": "Julián aparece."}],
                    }
                ]
            ),
            "Julián",
        ),
        (_plan(), _plan(title="La novela de Julián"), "Julián"),
        (
            _plan(),
            _plan(
                world={
                    "novum_description": "Las IA razonan sobre sus propios límites éticos.",
                    "novum_scope": "technological",
                    "novum_date": "2021-05-01",
                    "consequences": ["Una separación se hace pública.", "Otra."],
                }
            ),
            "separación",
        ),
    ],
    ids=["beat", "title", "consequence"],
)
async def test_a_banned_term_in_a_narrative_field_is_denied_and_corrected_in_the_same_session(
    clean_plan: dict[str, Any],
    dirty_plan: dict[str, Any],
    term: str,
    port: AgentPort,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    novel_id: int,
    plan_request: SessionRequest,
) -> None:
    ban(session_factory, level="novel", term="Julián", novel_id=novel_id)
    ban(
        session_factory,
        level="novel",
        term="divorcio",
        type_="topic",
        keywords=["divorcio", "separación"],
        novel_id=novel_id,
    )
    fake.script(
        "planner",
        "plan",
        Script(
            steps=(Call("submit_plan", dirty_plan), Call("submit_plan", clean_plan), Say("Listo."))
        ),
    )

    result = await port.run(plan_request)

    assert [c.status for c in result.calls] == ["denied", "accepted"]
    assert term in (result.calls[0].reason or "")
    assert len(fake.sessions) == 1
    rows = audit_rows(session_factory)
    assert [r["decision"] for r in rows] == ["deny", "allow"]
    assert rows[0]["rule"] == "palabras-prohibidas"
    assert rows[0]["origin"] == "policy_hook"
    assert rows[0]["tool"] == "submit_plan"


async def test_banned_terms_inside_the_avoid_lexicon_are_allowed(
    port: AgentPort,
    fake: FakeAgent,
    session_factory: sessionmaker[Session],
    novel_id: int,
    plan_request: SessionRequest,
) -> None:
    """La política no escanea el léxico a evitar (§7.5): ahí van a propósito."""
    ban(session_factory, level="novel", term="Julián", novel_id=novel_id)
    ban(
        session_factory,
        level="novel",
        term="divorcio",
        type_="topic",
        keywords=["divorcio", "separación"],
        novel_id=novel_id,
    )
    plan = _plan(
        style_sheet={
            "narrator": "third",
            "tense": "past",
            "default_treatment": "tu",
            "avoid_lexicon": ["Julián", "divorcio", "separación"],
        }
    )
    fake.script("planner", "plan", Script(steps=(Call("submit_plan", plan), Say("Listo."))))

    result = await port.run(plan_request)

    assert [c.status for c in result.calls] == ["accepted"]
    assert [r["decision"] for r in audit_rows(session_factory)] == ["allow"]


async def test_a_tool_outside_the_planner_whitelist_is_denied_and_is_not_a_delivery(
    port: AgentPort, fake: FakeAgent, plan_request: SessionRequest
) -> None:
    fake.script(
        "planner",
        "plan",
        Script(
            steps=(Call("Bash", {"command": "dir"}), Call("submit_plan", _plan()), Say("Listo."))
        ),
    )

    result = await port.run(plan_request)

    assert [(c.tool, c.status, c.own) for c in result.calls] == [
        ("Bash", "denied", False),
        ("submit_plan", "accepted", True),
    ]
    assert [c.tool for c in result.deliveries] == ["submit_plan"]

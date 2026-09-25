"""012-C6 · Una prohibida en la portada o en la ficha hace fallar la ejecución."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, cast

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed
from tests.pipeline.gate.conftest import (
    GateKit,
    gate_passes,
    results_of_pass,
    seed_unused_element,
)

from story_maker.agents.fake import FakeAgent
from story_maker.observability.port import Trace
from story_maker.pipeline.runs import RunStop
from story_maker.store.models import AuditLog, BannedTerm, Brief, Character, Fact, Novel, Place

TERM = "cuervo"


def _ban(session: Session, seed: Seed, level: str) -> None:
    session.add(
        BannedTerm(
            level=level,
            user_id=seed.user_id if level == "user" else None,
            term=TERM,
            type="word",
            normalized=TERM,
        )
    )


def _in_dedication(session: Session, seed: Seed) -> None:
    brief = session.query(Brief).filter(Brief.novel_id == seed.novel_id).one()
    brief.content = {"dedication": "Para ti, que viste el cuervo"}


def _in_title(session: Session, seed: Seed) -> None:
    session.get_one(Novel, seed.novel_id).title = "El cuervo del faro"


def _in_recipient_name(session: Session, seed: Seed) -> None:
    session.get_one(Character, seed.characters["Marta"]).canonical_name = "Marta Cuervo"


def _invented_place(session: Session, seed: Seed, name: str, description: str) -> None:
    session.add(
        Place(
            version_id=seed.version_id,
            canonical_name=name,
            description=description,
            origin="invented",
        )
    )


def _in_place_description(session: Session, seed: Seed) -> None:
    _invented_place(session, seed, "Cala Serena", "una cala donde anida un cuervo")


def _in_place_name(session: Session, seed: Seed) -> None:
    _invented_place(session, seed, "Roca del Cuervo", "una roca")


def _in_fact_value(session: Session, seed: Seed) -> None:
    session.get_one(Fact, seed.facts["rasgo"]).value = "le da miedo el cuervo"


def _plant(
    session_factory: sessionmaker[Session],
    seed: Seed,
    level: str,
    where: Callable[[Session, Seed], None],
) -> None:
    with session_factory() as session:
        _ban(session, seed, level)
        where(session, seed)
        session.commit()


def _gate_decisions(session_factory: sessionmaker[Session], run_id: int) -> list[AuditLog]:
    with session_factory() as session:
        return list(
            session.query(AuditLog)
            .filter(AuditLog.run_id == run_id, AuditLog.origin == "publication_gate")
            .all()
        )


def _locations(decision: AuditLog) -> set[str]:
    return {m["location"] for m in cast(list[dict[str, Any]], decision.detail)}


@pytest.mark.parametrize(
    ("level", "where", "location"),
    [
        ("user", _in_dedication, "cover"),
        ("global", _in_place_description, "sheet"),
    ],
    ids=["user-term-in-dedication", "global-term-in-invented-place-description"],
)
def test_a_banned_term_in_the_cover_or_the_sheet_fails_with_banned_content_without_rewrite(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    kit: GateKit,
    trace: Trace,
    level: str,
    where: Callable[[Session, Seed], None],
    location: str,
) -> None:
    seed_unused_element(session_factory, at_gate, chapters=(2, 5))
    _plant(session_factory, at_gate, level, where)

    with pytest.raises(RunStop) as stop:
        asyncio.run(kit.gate(at_gate.run_id, trace))

    assert (stop.value.status, stop.value.reason) == ("failed", "banned_content")
    assert fake.sessions == []
    assert kit.lean.calls == []
    assert gate_passes(session_factory, at_gate.run_id) == [(1, "fail")]
    [decision] = _gate_decisions(session_factory, at_gate.run_id)
    assert decision.decision == "deny"
    assert _locations(decision) == {location}
    banned = next(
        r
        for r in results_of_pass(session_factory, at_gate.run_id, 1)
        if r.validator == "palabras-prohibidas"
    )
    assert not banned.passed


@pytest.mark.parametrize(
    ("where", "location"),
    [
        (_in_title, "cover"),
        (_in_recipient_name, "cover"),
        (_in_dedication, "cover"),
        (_in_place_name, "sheet"),
        (_in_place_description, "sheet"),
        (_in_fact_value, "sheet"),
    ],
    ids=["title", "recipient-name", "dedication", "canonical-name", "description", "fact-value"],
)
def test_the_gate_scans_the_cover_and_every_character_and_place_of_the_sheet(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    kit: GateKit,
    trace: Trace,
    where: Callable[[Session, Seed], None],
    location: str,
) -> None:
    _plant(session_factory, at_gate, "global", where)

    with pytest.raises(RunStop) as stop:
        asyncio.run(kit.gate(at_gate.run_id, trace))

    assert (stop.value.status, stop.value.reason) == ("failed", "banned_content")
    [decision] = _gate_decisions(session_factory, at_gate.run_id)
    assert location in _locations(decision)

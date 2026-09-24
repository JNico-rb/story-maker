"""El `FicheroDeCronologia` desde SQLite (007-C06, 007-I6; la parte en SQLite de 007-C04 y
007-I3)."""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from story_maker.formal.generator import generate_chronology_file
from story_maker.formal.source import chronology_of_version
from story_maker.settings import ROOT
from story_maker.store import models
from story_maker.store.session import create_schema, make_engine, make_session_factory


def ids_in(source: str) -> dict[str, set[int]]:
    presences = re.findall(r"⟨(\d+), (?:none|some \d+)⟩", source)
    births = re.findall(r"⟨(\d+), ⟨\d+, \d+, \d+⟩⟩", source)
    excluded = re.findall(r"\.excluyente (\d+)", source)
    return {
        "events": {int(n) for n in re.findall(r"\{ id := (\d+),", source)},
        "places": {int(n) for n in re.findall(r"lugar := (\d+)", source)},
        "characters": {int(n) for n in [*presences, *births, *excluded]},
    }


def ids_of_version(session: Session, version_id: int) -> dict[str, set[int]]:
    events = session.query(models.Event).filter(models.Event.version_id == version_id)
    return {
        "events": {e.id for e in events if e.origin != "planned"},
        "all_events": {e.id for e in events},
        "places": {
            p.id for p in session.query(models.Place).filter(models.Place.version_id == version_id)
        },
        "characters": {
            c.id
            for c in session.query(models.Character).filter(
                models.Character.version_id == version_id
            )
        },
    }


# --- 007-C06, 007-I6 -------------------------------------------------------------------------


def test_only_the_version_being_verified_goes_into_the_file(store: Any, rows: Any) -> None:
    novel = store.novel()
    published = store.candidate(novel, rows.fixture_rows())
    store.publish(published)
    candidate = store.copy(published)
    with store.session() as session:
        place_id = min(ids_of_version(session, candidate)["places"])
        character_id = min(ids_of_version(session, candidate)["characters"])
    added = rows.event(None, dt.datetime(2026, 4, 1, 9, 30), place_id, origin="recorded", chapter=3)
    store.add(candidate, [added])
    with store.session() as session:
        added_id = max(ids_of_version(session, candidate)["all_events"])
    store.add(candidate, [rows.presence(added_id, character_id)])
    other = store.candidate(store.novel(), _other_novel_rows(rows))

    with store.session() as session:
        source = generate_chronology_file(chronology_of_version(session, candidate), k=2)
        mine = ids_of_version(session, candidate)
        theirs = [ids_of_version(session, published), ids_of_version(session, other)]

    written = ids_in(source)
    assert added_id in written["events"]
    assert written["events"] == mine["events"]
    for kind in ("events", "places", "characters"):
        assert written[kind] <= mine[kind]
        for version in theirs:
            assert written[kind].isdisjoint(version[kind] - mine[kind])
            assert written[kind].isdisjoint(version[kind])


# --- 007-C04 y 007-I3, desde SQLite ----------------------------------------------------------


def _write(tmp_path: Path, name: str, store_cls: Any, rows: list[Any]) -> str:
    engine = make_engine(tmp_path / f"{name}.db")
    create_schema(engine)
    factory: sessionmaker[Session] = make_session_factory(engine)
    store = store_cls(factory)
    version = store.candidate(store.novel(), rows)
    with store.session() as session:
        source = generate_chronology_file(chronology_of_version(session, version), k=3)
    engine.dispose()
    return source


def test_the_fixture_written_in_sqlite_in_two_insertion_orders_gives_the_golden_file(
    tmp_path: Path, store: Any, rows: Any
) -> None:
    in_order = rows.fixture_rows()
    by_kind: dict[type, list[Any]] = {}
    for row in rows.fixture_rows():  # filas nuevas: cada base de datos tiene las suyas
        by_kind.setdefault(type(row), []).append(row)
    reversed_rows = [row for kind in by_kind for row in reversed(by_kind[kind])]

    first = _write(tmp_path, "a", type(store), in_order)
    second = _write(tmp_path, "b", type(store), reversed_rows)

    assert first.encode("utf-8") == second.encode("utf-8")
    assert first.encode("utf-8") == (ROOT / "lean" / "pruebas" / "dorado.lean").read_bytes()


def test_no_name_or_statement_of_the_story_bible_reaches_the_file(
    tmp_path: Path, store: Any, rows: Any
) -> None:
    source = _write(tmp_path, "c", type(store), rows.fixture_rows())

    for text in rows.fixture_texts:
        assert text not in source


def _other_novel_rows(rows: Any) -> list[Any]:
    return [
        rows.character(211, "Ana", dt.date(1980, 1, 1)),
        rows.place(221, "el faro"),
        rows.event(231, dt.datetime(1999, 6, 1, 12, 0), 221),
        rows.presence(231, 211),
    ]

"""Solo una candidata admite escrituras (009-C21, 009-I1).

`store` es el atajo de `conftest.py` sobre el almacén de la prueba (tipo `Store`)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from typing import Any

import pytest
from sqlalchemy.orm import Session

from story_maker.store import models
from story_maker.store.session import UnitOfWork, unit_of_work
from story_maker.store.story_bible import change_fact_value
from story_maker.store.version_guard import VersionNotWritable

DIRECT = {
    "worlds": models.World,
    "characters": models.Character,
    "places": models.Place,
    "facts": models.Fact,
    "events": models.Event,
    "outline_chapters": models.OutlineChapter,
    "style_sheets": models.StyleSheet,
    "chapters": models.Chapter,
    "canon_cards": models.CanonCard,
}
TABLES = [*DIRECT, "fact_usages", "event_characters"]


def _first(session: Session, table: str, version_id: int) -> Any:
    if table == "fact_usages":
        return (
            session.query(models.FactUsage)
            .join(models.Fact, models.Fact.id == models.FactUsage.fact_id)
            .filter(models.Fact.version_id == version_id)
            .first()
        )
    if table == "event_characters":
        return (
            session.query(models.EventCharacter)
            .join(models.Event, models.Event.id == models.EventCharacter.event_id)
            .filter(models.Event.version_id == version_id)
            .first()
        )
    model = DIRECT[table]
    return session.query(model).filter(model.version_id == version_id).first()


def _absent_presence(session: Session, version_id: int) -> models.EventCharacter:
    """Un personaje de la versión en un evento suyo en el que todavía no está."""
    events = session.query(models.Event).filter_by(version_id=version_id).all()
    characters = session.query(models.Character).filter_by(version_id=version_id).all()
    for event in events:
        present = {
            p.character_id
            for p in session.query(models.EventCharacter).filter_by(event_id=event.id)
        }
        for character in characters:
            if character.id not in present:
                return models.EventCharacter(event_id=event.id, character_id=character.id)
    raise AssertionError("no hay presente libre")


def _new_row(session: Session, table: str, version_id: int) -> Any:
    """Una fila válida nueva de `table` en la versión (en una candidata de generación no choca)."""
    if table == "fact_usages":
        return models.FactUsage(fact_id=_first(session, "facts", version_id).id, chapter=10)
    if table == "event_characters":
        return _absent_presence(session, version_id)
    if table == "events":
        return models.Event(
            version_id=version_id,
            statement="nuevo",
            moment=dt.datetime(2026, 6, 1, 9, 0),
            place_id=_first(session, "places", version_id).id,
            type="ordinary",
            analepsis=False,
            origin="recorded",
            chapter=2,
            beat=1,
        )
    values: dict[str, dict[str, Any]] = {
        "worlds": {
            "novum_description": "n",
            "novum_scope": "social",
            "novum_date": dt.date(2020, 1, 1),
            "consequences": ["a", "b"],
        },
        "characters": {
            "type": "invented",
            "species": "person",
            "canonical_name": "Nuevo",
            "origin": "invented",
        },
        "places": {"canonical_name": "nuevo", "description": "", "origin": "invented"},
        "facts": {
            "subject_type": "world",
            "attribute": "x",
            "value": "y",
            "origin": "invented",
            "mandatory": False,
        },
        "outline_chapters": {
            "number": 1,
            "title": "t",
            "arc_function": "f",
            "beats": [],
            "assigned_elements": [],
        },
        "style_sheets": {"content": {}},
        "chapters": {
            "number": 1,
            "title": "t",
            "text": "x",
            "summary": "s",
            "word_count": 1000,
            "content_hash": "h",
        },
        "canon_cards": {
            "entity_type": "world",
            "from_chapter": 1,
            "text": "t",
            "content_hash": "h",
        },
    }
    return DIRECT[table](version_id=version_id, **values[table])


MODIFY: dict[str, Callable[[Any], None]] = {
    "worlds": lambda r: setattr(r, "novum_description", "otro novum"),
    "characters": lambda r: setattr(r, "canonical_name", r.canonical_name + "x"),
    "places": lambda r: setattr(r, "description", "otra descripción"),
    "facts": lambda r: setattr(r, "value", r.value + "x"),
    "fact_usages": lambda r: setattr(r, "chapter", 9 if r.chapter != 9 else 8),
    "events": lambda r: setattr(r, "statement", "otro enunciado"),
    "event_characters": lambda r: setattr(r, "declared_age", 99),
    "outline_chapters": lambda r: setattr(r, "title", "otro título"),
    "style_sheets": lambda r: setattr(r, "content", {"otro": True}),
    "chapters": lambda r: setattr(r, "title", "otro título"),
    "canon_cards": lambda r: setattr(r, "text", "otro texto"),
}

VERSION_ROW_CHANGES: dict[str, Callable[[models.Version], None]] = {
    "number": lambda v: setattr(v, "number", 7),
    "base_version_id": lambda v: setattr(v, "base_version_id", None if v.base_version_id else 1),
    "changed_chapters": lambda v: setattr(v, "changed_chapters", [1]),
    "pdf_path": lambda v: setattr(v, "pdf_path", "otro.pdf"),
    "created_at": lambda v: setattr(v, "created_at", dt.datetime(2020, 1, 1)),
    "published_at": lambda v: setattr(v, "published_at", dt.datetime(2020, 1, 1)),
}


def _write(store: Any, operation: Callable[[UnitOfWork], object]) -> None:
    with unit_of_work(store.session_factory) as uow:
        operation(uow)


def _writes(table: str, version_id: int) -> dict[str, Callable[[UnitOfWork], None]]:
    """Insertar, modificar y borrar una fila de `table` en la versión."""

    def insert(uow: UnitOfWork) -> None:
        uow.add(_new_row(uow.session, table, version_id))

    def modify(uow: UnitOfWork) -> None:
        MODIFY[table](_first(uow.session, table, version_id))

    def delete(uow: UnitOfWork) -> None:
        uow.delete(_first(uow.session, table, version_id))

    return {"insert": insert, "modify": modify, "delete": delete}


def _terminal_versions(store: Any) -> dict[str, tuple[int, str]]:
    """v1 publicada y K3 descartada, cada una con todas sus tablas de ámbito versión llenas."""
    v1 = store.build_v1()
    k3_id, _ = store.copy(v1.version_id)
    store.discard(k3_id)
    return {"v1": (v1.version_id, "publicada"), "K3": (k3_id, "descartada")}


def _assert_rejected(store: Any, operation: Any, version_id: int, state: str, label: Any) -> None:
    before = store.fingerprint(version_id)
    with pytest.raises(VersionNotWritable) as rejected:
        _write(store, operation)
    assert f"versión {version_id}" in str(rejected.value), label
    assert state in str(rejected.value), label
    assert store.fingerprint(version_id) == before, label


@pytest.mark.parametrize("table", TABLES)
def test_a_published_or_discarded_version_rejects_every_write_to_its_tables(
    store: Any, table: str
) -> None:
    for name, (version_id, state) in _terminal_versions(store).items():
        for kind, operation in _writes(table, version_id).items():
            _assert_rejected(store, operation, version_id, state, (name, kind))


def test_a_published_or_discarded_version_rejects_changing_a_fact_or_its_row(
    store: Any,
) -> None:
    for name, (version_id, state) in _terminal_versions(store).items():
        with store.session() as session:
            facts = session.query(models.Fact).filter_by(version_id=version_id).all()
            fact_ids = [f.id for f in facts[:2]]  # el hecho de nombre de Marta y un rasgo
        for fact_id in fact_ids:

            def change_fact(uow: UnitOfWork, fact_id: int = fact_id) -> None:
                change_fact_value(uow, fact_id, "otro")

            _assert_rejected(store, change_fact, version_id, state, (name, fact_id))
        for column, change in VERSION_ROW_CHANGES.items():

            def change_row(uow: UnitOfWork, change: Any = change, v: int = version_id) -> None:
                change(uow.session.get(models.Version, v))

            _assert_rejected(store, change_row, version_id, state, (name, column))


@pytest.mark.parametrize("table", TABLES)
def test_a_candidate_accepts_writes_to_its_tables(store: Any, f1: Any, table: str) -> None:
    k4_id = store.generation(store.new_novel(), f1)
    created: list[Any] = []

    def insert(uow: UnitOfWork) -> None:
        row = _new_row(uow.session, table, k4_id)
        uow.add(row)
        created.append(row)

    _write(store, insert)
    row_type, row_id = type(created[0]), created[0].id
    if table != "canon_cards":  # una CanonCard no se edita: se sucede (001-C11)
        _write(store, lambda uow: MODIFY[table](uow.session.get(row_type, row_id)))
    _write(store, lambda uow: uow.delete(uow.session.get(row_type, row_id)))
    _write(store, lambda uow: change_fact_value(uow, _first(uow.session, "facts", k4_id).id, "z"))

    with store.session() as session:
        assert session.get(row_type, row_id) is None

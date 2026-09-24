"""Sesión de SQLite: WAL, claves ajenas, canal denso y unidad de trabajo (C6-C13)."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import sqlite_vec
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from story_maker.store.models import CANON_CARDS_FTS_DDL, INSERT_ONLY_TABLES, Base, CanonCard


class RejectedWrite(ValueError):
    """Intento de modificar o borrar una fila de solo inserción, o de editar una CanonCard."""


def _on_connect(dbapi_connection: sqlite3.Connection, _record: object) -> None:
    dbapi_connection.enable_load_extension(True)
    sqlite_vec.load(dbapi_connection)
    dbapi_connection.enable_load_extension(False)
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def make_engine(db_path: Path) -> Engine:
    """Motor SQLAlchemy que abre `db_path` igual en toda conexión (C8)."""
    from sqlalchemy import create_engine

    engine = create_engine(f"sqlite:///{db_path}", future=True)
    event.listen(engine, "connect", _on_connect)
    return engine


def create_schema(engine: Engine) -> None:
    """Crea las 31 tablas y el índice FTS5 de las CanonCards (C6)."""
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text(CANON_CARDS_FTS_DDL))


def schema_diff(engine: Engine) -> list[str]:
    """Tablas o columnas que le faltan o le sobran a `engine` frente al esquema de C6 (C14)."""
    problems: list[str] = []
    with engine.connect() as connection:
        actual_tables = {
            row[0]
            for row in connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        }
        for table in Base.metadata.sorted_tables:
            if table.name not in actual_tables:
                problems.append(f"falta la tabla {table.name}")
                continue
            actual_columns = {
                row[1] for row in connection.execute(text(f"PRAGMA table_info({table.name})"))
            }
            expected_columns = {column.name for column in table.columns}
            missing = sorted(expected_columns - actual_columns)
            extra = sorted(actual_columns - expected_columns)
            problems += [f"falta la columna {table.name}.{c}" for c in missing]
            problems += [f"sobra la columna {table.name}.{c}" for c in extra]
    return problems


def dense_channel_ok(engine: Engine) -> bool:
    """El canal denso (`sqlite-vec`) responde en `engine` (C8, C14)."""
    try:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT vec_distance_cosine(:a, :b)"),
                {
                    "a": sqlite_vec.serialize_float32([1, 0]),
                    "b": sqlite_vec.serialize_float32([0, 1]),
                },
            )
        return True
    except Exception:
        return False


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


class UnitOfWork:
    """Todo o nada (C13); rechaza tocar una tabla de solo inserción o editar una CanonCard (C11);
    mantiene el índice FTS5 sincronizado con las CanonCards, en la misma transacción (C12)."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self._new_cards: list[CanonCard] = []
        self._deleted_cards: list[CanonCard] = []

    def add(self, obj: Any) -> None:
        if isinstance(obj, CanonCard):
            self._new_cards.append(obj)
        self.session.add(obj)

    def delete(self, obj: Any) -> None:
        if isinstance(obj, INSERT_ONLY_TABLES):
            raise RejectedWrite(f"{type(obj).__tablename__} es de solo inserción")
        if isinstance(obj, CanonCard):
            self._deleted_cards.append(obj)
        self.session.delete(obj)

    def _reject_modified_insert_only(self) -> None:
        for obj in list(self.session.dirty):
            if isinstance(obj, INSERT_ONLY_TABLES):
                raise RejectedWrite(f"{type(obj).__tablename__} es de solo inserción")
            if isinstance(obj, CanonCard):
                raise RejectedWrite("canon_cards no se edita, se sucede")

    def commit(self) -> None:
        self._reject_modified_insert_only()
        self.session.flush()
        for card in self._new_cards:
            self.session.execute(
                text("INSERT INTO canon_cards_fts(rowid, text) VALUES (:id, :text)"),
                {"id": card.id, "text": card.text},
            )
        for card in self._deleted_cards:
            self.session.execute(
                text(
                    "INSERT INTO canon_cards_fts(canon_cards_fts, rowid, text) "
                    "VALUES ('delete', :id, :text)"
                ),
                {"id": card.id, "text": card.text},
            )
        self.session.commit()
        self._new_cards.clear()
        self._deleted_cards.clear()

    def rollback(self) -> None:
        self.session.rollback()
        self._new_cards.clear()
        self._deleted_cards.clear()

    def __enter__(self) -> UnitOfWork:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()


@contextmanager
def unit_of_work(session_factory: sessionmaker[Session]) -> Iterator[UnitOfWork]:
    session = session_factory()
    try:
        with UnitOfWork(session) as uow:
            yield uow
    finally:
        session.close()

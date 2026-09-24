"""Datos compartidos de la spec 007: la cronología de fixture («Datos de los casos») y la tabla
de salidas de la compilación de 007-C13, que 007-C15 repite por el modo github."""

from __future__ import annotations

import datetime as dt
import itertools
import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker

from story_maker.formal.chronology import (
    Chronology,
    ChronologyCharacter,
    ChronologyEvent,
    Presence,
)
from story_maker.formal.lean_output import LeanOutput
from story_maker.formal.result import INVARIANTS, ChronologyResult, Invariant
from story_maker.store import models
from story_maker.store.session import (
    create_schema,
    make_engine,
    make_session_factory,
    unit_of_work,
)
from story_maker.store.version_copy import copy_version
from story_maker.store.versions import publish

RECIPIENT, GRANDMOTHER, DOG = 11, 12, 13
PLACE_A, PLACE_B = 21, 22


def fixture_chronology() -> Chronology:
    """El destinatario (11), la abuela (12), el perro (13); lugares 21 y 22; eventos 31, 32 (brief),
    41, 42 (registrados) y 51 (planificado)."""
    return Chronology(
        events=(
            ChronologyEvent(
                id=31,
                moment=dt.datetime(1998, 5, 14, 12, 0),
                place_id=PLACE_A,
                presences=(Presence(RECIPIENT, 8), Presence(GRANDMOTHER)),
                type="ordinary",
                excluded_character_id=None,
                analepsis=False,
                origin="brief",
                chapter=None,
                beat=None,
            ),
            ChronologyEvent(
                id=32,
                moment=dt.datetime(2010, 9, 1, 12, 0),
                place_id=PLACE_B,
                presences=(Presence(RECIPIENT),),
                type="exclusion",
                excluded_character_id=GRANDMOTHER,
                analepsis=False,
                origin="brief",
                chapter=None,
                beat=None,
            ),
            ChronologyEvent(
                id=41,
                moment=dt.datetime(2026, 3, 2, 10, 0),
                place_id=PLACE_A,
                presences=(Presence(RECIPIENT), Presence(DOG)),
                type="ordinary",
                excluded_character_id=None,
                analepsis=False,
                origin="recorded",
                chapter=1,
                beat=1,
            ),
            ChronologyEvent(
                id=42,
                moment=dt.datetime(2005, 7, 1, 18, 0),
                place_id=PLACE_B,
                presences=(Presence(RECIPIENT), Presence(GRANDMOTHER)),
                type="ordinary",
                excluded_character_id=None,
                analepsis=True,
                origin="recorded",
                chapter=2,
                beat=1,
            ),
            ChronologyEvent(
                id=51,
                moment=dt.datetime(2026, 5, 10, 9, 0),
                place_id=PLACE_A,
                presences=(Presence(RECIPIENT),),
                type="ordinary",
                excluded_character_id=None,
                analepsis=False,
                origin="planned",
                chapter=3,
                beat=2,
            ),
        ),
        characters=(
            ChronologyCharacter(RECIPIENT, dt.date(1990, 5, 14)),
            ChronologyCharacter(GRANDMOTHER, dt.date(1936, 2, 29)),
            ChronologyCharacter(DOG, None),
        ),
        novum_date=dt.date(2024, 11, 1),
    )


@pytest.fixture
def chronology() -> Chronology:
    return fixture_chronology()


# --- Tabla de 007-C13: salida de la compilación → resultado -----------------------------------

ADMITTED = ["propext", "Classical.choice", "Quot.sound"]


def report(**violated: list[int]) -> dict[str, Any]:
    """JSON del informe: cumplen todos salvo los violados, con su testigo."""
    return {
        t: {"cumple": False, "testigo": violated[t]} if t in violated else {"cumple": True}
        for t in INVARIANTS
    }


def audits(**overrides: list[str]) -> dict[str, list[str]]:
    """Axiomas de cada teorema `cumpleTn`: admitidos salvo los que se indiquen."""
    return {f"cumple{t}": overrides.get(t, ["propext"]) for t in INVARIANTS}


def lean_text(
    json_report: dict[str, Any] | None,
    axioms: dict[str, list[str]],
    errors: tuple[str, ...] = (),
    prefix: str = "",
) -> str:
    """Salida con la forma de `lean`: diagnósticos, la línea del informe y `#print axioms`."""
    lines = [f"Cronologia.lean:{30 + i}:0: error: {e}" for i, e in enumerate(errors)]
    if json_report is not None:
        lines.append(f"{prefix}CRONOLOGIA-LEAN {json.dumps(json_report, separators=(',', ':'))}")
    for name, used in axioms.items():
        if used:
            lines.append(f"{prefix}'{name}' depends on axioms: [{', '.join(used)}]")
        else:
            lines.append(f"{prefix}'{name}' does not depend on any axioms")
    return "\n".join(lines) + "\n"


ALL_HOLD: dict[Invariant, bool] = dict.fromkeys(INVARIANTS, True)


@dataclass(frozen=True)
class LeanRow:
    name: str
    output: LeanOutput
    expected: str
    holds: dict[Invariant, bool] = field(default_factory=dict)
    witnesses: dict[Invariant, tuple[int, ...]] = field(default_factory=dict)
    reason_contains: tuple[str, ...] = ()

    def check(self, result: ChronologyResult) -> None:
        assert result.result == self.expected, result
        assert dict(result.holds) == self.holds
        assert dict(result.witnesses) == self.witnesses
        for fragment in self.reason_contains:
            assert result.reason is not None
            assert fragment in result.reason, result.reason


LEAN_ROWS = (
    LeanRow(
        "compila-cumple-todo",
        LeanOutput(0, lean_text(report(), audits(T2=ADMITTED, T5=[]))),
        "passed",
        holds=ALL_HOLD,
    ),
    LeanRow(
        "compila-cumple-todo-con-prefijo",
        LeanOutput(0, lean_text(report(), audits(), prefix="Cronologia.lean:12:0: info: ")),
        "passed",
        holds=ALL_HOLD,
    ),
    LeanRow(
        "no-compila-T4",
        LeanOutput(
            1,
            lean_text(
                report(T4=[12, 32, 71]),
                audits(T4=["propext", "sorryAx"]),
                errors=("decide failed: proposition compruebaT4 cronologia = true is false",),
            ),
        ),
        "failed",
        holds={**ALL_HOLD, "T4": False},
        witnesses={"T4": (12, 32, 71)},
    ),
    LeanRow(
        "no-compila-cumple-todo",
        LeanOutput(1, lean_text(report(), audits(), errors=("unknown identifier 'x'",))),
        "error",
        reason_contains=("unknown identifier 'x'",),
    ),
    LeanRow(
        "no-compila-sin-json",
        LeanOutput(1, lean_text(None, {}, errors=("unexpected token 'eventos'",))),
        "error",
        reason_contains=("unexpected token 'eventos'",),
    ),
    LeanRow(
        "compila-con-invariante-violado",
        LeanOutput(0, lean_text(report(T2=[11, 31, 9, 8]), audits())),
        "error",
        reason_contains=("incoherentes",),
    ),
    LeanRow(
        "auditoria-sorry",
        LeanOutput(0, lean_text(report(), audits(T3=["propext", "sorryAx"]))),
        "error",
        reason_contains=("cumpleT3", "sorryAx"),
    ),
    LeanRow(
        "auditoria-axioma-propio",
        LeanOutput(0, lean_text(report(), audits(T1=["trampa"]))),
        "error",
        reason_contains=("cumpleT1", "trampa"),
    ),
)


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "lean_row" in metafunc.fixturenames:
        metafunc.parametrize("lean_row", LEAN_ROWS, ids=[row.name for row in LEAN_ROWS])


class LeanTexts:
    """Los constructores de salidas de `lean` de esta conftest, para otros módulos de prueba."""

    report = staticmethod(report)
    audits = staticmethod(audits)
    text = staticmethod(lean_text)
    admitted = ADMITTED


@pytest.fixture
def lean_texts() -> type[LeanTexts]:
    return LeanTexts


# --- Almacén SQLite de las pruebas de la 007 (007-C04, 007-C06, 007-C09 a 007-C12) ------------

NOW = dt.datetime(2026, 9, 24, 12, 0)


class FormalStore:
    """Escribe story bibles, versiones y ejecuciones con los ids que se le den, como la spec."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory
        self._users = itertools.count(1)

    def session(self) -> Session:
        return self.session_factory()

    def novel(self) -> int:
        with unit_of_work(self.session_factory) as uow:
            n = next(self._users)
            user = models.User(email=f"u{n}@example.com", password_hash="h", created_at=NOW)
            uow.add(user)
            uow.session.flush()
            novel = models.Novel(user_id=user.id, title=None, embedding_model="m", created_at=NOW)
            uow.add(novel)
        return novel.id

    def candidate(self, novel_id: int, rows: list[Any]) -> int:
        """Una candidata con su mundo y las filas dadas (personajes, lugares, eventos,
        presencias), en ese orden de inserción."""
        with unit_of_work(self.session_factory) as uow:
            version = models.Version(
                novel_id=novel_id, status="candidate", changed_chapters=[], created_at=NOW
            )
            uow.add(version)
            uow.session.flush()
            uow.add(
                models.World(
                    version_id=version.id,
                    novum_description="las máquinas aprendieron a recordar",
                    novum_scope="technological",
                    novum_date=dt.date(2024, 11, 1),
                    consequences=["nadie olvida", "los recuerdos se venden"],
                )
            )
            for row in rows:
                if not isinstance(row, models.EventCharacter):
                    row.version_id = version.id
                uow.add(row)
                uow.session.flush()
        return version.id

    def publish(self, version_id: int) -> None:
        with unit_of_work(self.session_factory) as uow:
            publish(uow, version_id, pdf_path="v.pdf", now=NOW)

    def copy(self, version_id: int) -> int:
        with unit_of_work(self.session_factory) as uow:
            return copy_version(uow, version_id, now=NOW).version.id

    def add(self, version_id: int, rows: list[Any]) -> None:
        with unit_of_work(self.session_factory) as uow:
            for row in rows:
                if not isinstance(row, models.EventCharacter):
                    row.version_id = version_id
                uow.add(row)
                uow.session.flush()

    def run(self, novel_id: int, candidate_id: int) -> int:
        with unit_of_work(self.session_factory) as uow:
            run = models.Run(
                novel_id=novel_id,
                type="generation",
                status="running",
                phase="gate",
                candidate_version_id=candidate_id,
                resumes=0,
                created_at=NOW,
            )
            uow.add(run)
        return run.id

    def chronology_files(self) -> list[models.ChronologyFile]:
        with self.session() as session:
            return list(session.query(models.ChronologyFile).order_by(models.ChronologyFile.id))


def character(id_: int, name: str, birth: dt.date | None) -> models.Character:
    return models.Character(
        id=id_,
        type="close_one",
        species="person",
        canonical_name=name,
        birth_date=birth,
        origin="brief",
    )


def place(id_: int, name: str) -> models.Place:
    return models.Place(
        id=id_, canonical_name=name, description=f"{name}, de cerca", origin="brief"
    )


def event(
    id_: int | None,
    moment: dt.datetime,
    place_id: int,
    *,
    statement: str = "algo pasa",
    origin: str = "brief",
    excluded: int | None = None,
    analepsis: bool = False,
    chapter: int | None = None,
    beat: int | None = None,
) -> models.Event:
    return models.Event(
        id=id_,
        statement=statement,
        moment=moment,
        place_id=place_id,
        type="exclusion" if excluded is not None else "ordinary",
        excluded_character_id=excluded,
        analepsis=analepsis,
        origin=origin,
        chapter=chapter,
        beat=beat,
    )


def presence(event_id: int, character_id: int, age: int | None = None) -> models.EventCharacter:
    return models.EventCharacter(event_id=event_id, character_id=character_id, declared_age=age)


def fixture_rows() -> list[Any]:
    """La cronología de fixture de la spec, con sus nombres y enunciados, como filas."""
    return [
        character(11, "Marta", dt.date(1990, 5, 14)),
        character(12, "Rosa", dt.date(1936, 2, 29)),
        character(13, "Toby", None),
        place(21, "la feria del pueblo"),
        place(22, "la estación"),
        event(31, dt.datetime(1998, 5, 14, 12, 0), 21, statement="se perdió en la feria"),
        event(32, dt.datetime(2010, 9, 1, 12, 0), 22, statement="Rosa se marchó", excluded=12),
        event(
            41,
            dt.datetime(2026, 3, 2, 10, 0),
            21,
            statement="vuelven a la feria",
            origin="recorded",
            chapter=1,
            beat=1,
        ),
        event(
            42,
            dt.datetime(2005, 7, 1, 18, 0),
            22,
            statement="la despedida en el andén",
            origin="recorded",
            chapter=2,
            beat=1,
            analepsis=True,
        ),
        event(
            51,
            dt.datetime(2026, 5, 10, 9, 0),
            21,
            statement="planean el viaje",
            origin="planned",
            chapter=3,
            beat=2,
        ),
        presence(31, 11, 8),
        presence(31, 12),
        presence(32, 11),
        presence(41, 11),
        presence(41, 13),
        presence(42, 11),
        presence(42, 12),
        presence(51, 11),
    ]


FIXTURE_TEXTS = [
    "Marta",
    "Rosa",
    "Toby",
    "la feria del pueblo",
    "la estación",
    "se perdió en la feria",
    "Rosa se marchó",
    "vuelven a la feria",
    "la despedida en el andén",
    "planean el viaje",
]


class Rows:
    """Los constructores de filas, para los módulos de prueba (que no importan la conftest)."""

    character = staticmethod(character)
    place = staticmethod(place)
    event = staticmethod(event)
    presence = staticmethod(presence)
    fixture_rows = staticmethod(fixture_rows)
    fixture_texts = FIXTURE_TEXTS


@pytest.fixture
def session_factory(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = make_engine(tmp_path / "story-maker.db")
    create_schema(engine)
    yield make_session_factory(engine)
    engine.dispose()


@pytest.fixture
def store(session_factory: sessionmaker[Session]) -> FormalStore:
    return FormalStore(session_factory)


@pytest.fixture
def rows() -> type[Rows]:
    return Rows

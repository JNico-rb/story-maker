"""Datos de las pruebas de la 009 (F1, F2), construidos directamente en el almacén."""

from __future__ import annotations

import datetime as dt
import hashlib
import itertools
import json
from dataclasses import dataclass
from typing import Any

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session, sessionmaker

from story_maker.store import models
from story_maker.store.brief_canon import (
    NAME,
    BriefCloseOne,
    BriefExtractedFact,
    BriefRecipient,
    BriefRecollection,
    BriefTrait,
    ConfirmedBrief,
    create_generation_candidate,
)
from story_maker.store.models import Novel, User
from story_maker.store.session import UnitOfWork, unit_of_work
from story_maker.store.version_copy import copy_version

CREATED_2026 = dt.datetime(2026, 9, 24, 10, 0)
NOW = dt.datetime(2026, 9, 24, 11, 0)

_emails = itertools.count(1)


def f1_brief() -> ConfirmedBrief:
    """F1: Marta, 40 años; Toby, Luis y Rosa; R1, R2 y R3; X1 aceptado y X2 sin aceptar."""
    return ConfirmedBrief(
        recipient=BriefRecipient(
            name="Marta",
            age=40,
            name_element_id=1,
            traits=(
                BriefTrait("curiosa", element_id=2, mandatory=False),
                BriefTrait("le encanta el mar", element_id=3, mandatory=True),
            ),
        ),
        close_ones=(
            BriefCloseOne("Toby", "perro", "animal", element_id=4, mandatory=True),
            BriefCloseOne("Luis", "hermano", "person", element_id=5, mandatory=False, age=37),
            BriefCloseOne("Rosa", "abuela", "person", element_id=6, mandatory=False),
        ),
        recollections=(
            BriefRecollection(
                "se perdió en la feria de su pueblo",
                "la feria del pueblo",
                element_id=7,
                mandatory=True,
                age=8,
                present=("Luis",),
            ),
            BriefRecollection(
                "su primer baño en el mar",
                "la playa del faro",
                element_id=8,
                mandatory=False,
                year=1990,
            ),
            BriefRecollection(
                "la abuela Rosa se marchó para siempre",
                "la estación",
                element_id=9,
                mandatory=False,
                age=12,
                present=("Rosa",),
                excluded="Rosa",
            ),
        ),
        extracted_facts=(
            BriefExtractedFact(
                "Marta",
                "comida favorita",
                "la paella",
                accepted=True,
                mandatory=True,
                element_id=10,
            ),
            BriefExtractedFact("Toby", "color", "negro", accepted=False, mandatory=False),
        ),
    )


def f2_brief() -> ConfirmedBrief:
    """F2: Leo, nacido el 2000-02-29, con recuerdos a los 0, 4 y 5 años y en 2000 y 2010."""
    ages = [(0, "a los 0"), (4, "a los 4"), (5, "a los 5")]
    years = [(2000, "en 2000"), (2010, "en 2010")]
    recollections = [
        BriefRecollection(
            f"recuerdo {label}", f"lugar {label}", element_id=10 + i, mandatory=False, age=age
        )
        for i, (age, label) in enumerate(ages)
    ] + [
        BriefRecollection(
            f"recuerdo {label}", f"lugar {label}", element_id=20 + i, mandatory=False, year=year
        )
        for i, (year, label) in enumerate(years)
    ]
    return ConfirmedBrief(
        recipient=BriefRecipient(
            name="Leo",
            age=26,
            name_element_id=1,
            traits=(BriefTrait("tranquilo", element_id=2, mandatory=False),),
            birth_date=dt.date(2000, 2, 29),
        ),
        recollections=tuple(recollections),
    )


@dataclass
class Store:
    """Atajos sobre el almacén de la prueba; cada operación, en su unidad de trabajo."""

    session_factory: sessionmaker[Session]
    now: dt.datetime = NOW

    def session(self) -> Session:
        return self.session_factory()

    def new_novel(self, created_at: dt.datetime = CREATED_2026, model: str = "m1") -> int:
        with unit_of_work(self.session_factory) as uow:
            user = User(email=f"c{next(_emails)}@example.com", password_hash="h", created_at=NOW)
            uow.add(user)
            uow.session.flush()
            novel = Novel(user_id=user.id, title=None, embedding_model=model, created_at=created_at)
            uow.add(novel)
        return novel.id

    def generation(self, novel_id: int, brief: ConfirmedBrief, now: dt.datetime = NOW) -> int:
        with unit_of_work(self.session_factory) as uow:
            novel = uow.session.get(Novel, novel_id)
            assert novel is not None
            version = create_generation_candidate(uow, novel, brief, now=now)
        return version.id

    def build_v1(self) -> V1:
        """V1: el canon de F1 más mundo, Iris, el mercado de datos, P1, E4, E5, outline,
        StyleSheet, 10 capítulos, `UsoDeHecho` y CanonCards con sus vectores; publicada."""
        novel_id = self.new_novel()
        version_id = self.generation(novel_id, f1_brief())
        with unit_of_work(self.session_factory) as uow:
            session = uow.session
            version = session.get(models.Version, version_id)
            assert version is not None
            novel = session.get(models.Novel, novel_id)
            assert novel is not None
            chars = {c.canonical_name: c for c in _of(session, models.Character, version_id)}
            places = {p.canonical_name: p for p in _of(session, models.Place, version_id)}

            world = models.World(
                version_id=version_id,
                novum_description="las IA aprendieron a soñar",
                novum_scope="technological",
                novum_date=dt.date(2019, 5, 1),
                consequences=["los sueños se comparten", "nadie duerme solo"],
            )
            iris = models.Character(
                version_id=version_id,
                type="invented",
                species="artificial",
                canonical_name="Iris",
                birth_date=None,
                origin="invented",
            )
            market = models.Place(
                version_id=version_id,
                canonical_name="el mercado de datos",
                description="un mercado de recuerdos",
                origin="invented",
            )
            for row in (world, iris, market):
                uow.add(row)
            session.flush()
            chars["Iris"] = iris
            places["el mercado de datos"] = market
            uow.add(
                models.Fact(
                    version_id=version_id,
                    subject_type="world",
                    attribute="ley",
                    value="soñar está regulado",
                    origin="invented",
                    mandatory=False,
                )
            )
            uow.add(
                models.Fact(
                    version_id=version_id,
                    subject_type="character",
                    character_id=iris.id,
                    attribute=NAME,
                    value="Iris",
                    origin="invented",
                    mandatory=False,
                )
            )
            session.flush()
            facts = {f.value: f for f in _of(session, models.Fact, version_id)}

            feria = places["la feria del pueblo"]
            planned = [
                (
                    "P1: Marta vuelve a la feria",
                    dt.datetime(2026, 5, 10, 17, 0),
                    feria,
                    ["Marta"],
                    "planned",
                    1,
                    2,
                ),
                (
                    "E4: Marta y Toby en la feria",
                    dt.datetime(2026, 5, 10, 18, 0),
                    feria,
                    ["Marta", "Toby"],
                    "recorded",
                    1,
                    2,
                ),
                (
                    "E5: Marta e Iris en el mercado",
                    dt.datetime(2026, 5, 12, 10, 0),
                    market,
                    ["Marta", "Iris"],
                    "recorded",
                    3,
                    1,
                ),
            ]
            for statement, moment, place, present, origin, chapter, beat in planned:
                event = models.Event(
                    version_id=version_id,
                    statement=statement,
                    moment=moment,
                    place_id=place.id,
                    type="ordinary",
                    analepsis=False,
                    origin=origin,
                    chapter=chapter,
                    beat=beat,
                )
                uow.add(event)
                session.flush()
                for name in present:
                    uow.add(models.EventCharacter(event_id=event.id, character_id=chars[name].id))

            for n in range(1, 11):
                uow.add(
                    models.OutlineChapter(
                        version_id=version_id,
                        number=n,
                        title=f"Capítulo {n}",
                        arc_function="desarrollo",
                        beats=[{"number": 1, "description": f"beat del capítulo {n}"}],
                        assigned_elements=[1] if n == 1 else [],
                    )
                )
                title, text = f"Capítulo {n}", f"Texto del capítulo {n}, con Marta."
                uow.add(
                    models.Chapter(
                        version_id=version_id,
                        number=n,
                        title=title,
                        text=text,
                        summary=f"Resumen {n}",
                        word_count=1200,
                        content_hash=chapter_hash(title, text),
                    )
                )
            uow.add(models.StyleSheet(version_id=version_id, content={"narrator": "third_person"}))

            usages = [("Marta", n) for n in range(1, 11)] + [("Toby", 3), ("Toby", 7)]
            usages.append(("la paella", 5))
            for value, chapter in usages:
                uow.add(models.FactUsage(fact_id=facts[value].id, chapter=chapter))

            cards = [("character", chars[name], None, 1, f"{name}.") for name in chars]
            cards[0] = (
                "character",
                chars["Marta"],
                None,
                1,
                "Marta, curiosa; se perdió en la feria.",
            )
            cards.append(
                ("character", chars["Marta"], None, 4, "Marta volvió a la feria con Toby.")
            )
            cards += [("place", None, p, 1, f"Lugar: {name}.") for name, p in places.items()]
            cards.append(("world", None, None, 1, "Las IA aprendieron a soñar."))
            for entity_type, character, place, from_chapter, text in cards:
                card_hash = hashlib.sha256(text.encode()).hexdigest()
                uow.add(
                    models.CanonCard(
                        version_id=version_id,
                        entity_type=entity_type,
                        character_id=character.id if character else None,
                        place_id=place.id if place else None,
                        from_chapter=from_chapter,
                        text=text,
                        content_hash=card_hash,
                    )
                )
                uow.add(
                    models.Embedding(
                        content_hash=card_hash, model=novel.embedding_model, vector=bytes(8)
                    )
                )

            version.status = "published"
            version.number = 1
            version.published_at = NOW
        return V1(
            novel_id=novel_id,
            version_id=version_id,
            characters={name: c.id for name, c in chars.items()},
            places={name: p.id for name, p in places.items()},
            facts={value: f.id for value, f in facts.items()},
        )

    def copy(self, base_id: int, now: dt.datetime = NOW) -> tuple[int, dict[str, dict[int, int]]]:
        """Copia la versión `base_id`: el id de la candidata y la traducción de ids."""
        with unit_of_work(self.session_factory) as uow:
            base = uow.session.get(models.Version, base_id)
            assert base is not None
            copied = copy_version(uow, base, now=now)
        return copied.version.id, {t: dict(m) for t, m in copied.ids.items()}

    def dump(self, version_id: int) -> dict[str, list[dict[str, Any]]]:
        """La fila de la versión y todas sus filas de ámbito versión, tabla a tabla."""
        with self.session() as session:
            version = session.get(models.Version, version_id)
            assert version is not None
            out = {"versions": [_as_dict(version)]}
            for model in VERSION_SCOPED:
                out[model.__tablename__] = [_as_dict(r) for r in _of(session, model, version_id)]
            card_ids = [c["id"] for c in out["canon_cards"]]
            fts = session.execute(
                text(
                    "SELECT rowid, text FROM canon_cards_fts WHERE rowid IN (SELECT value FROM "
                    "json_each(:ids)) ORDER BY rowid"
                ),
                {"ids": json.dumps(card_ids)},
            )
            out["canon_cards_fts"] = [{"rowid": r[0], "text": r[1]} for r in fts]
            return out

    def fingerprint(self, version_id: int) -> str:
        """La huella de una versión: su fila y todas sus filas de ámbito versión (009-C13)."""
        dumped = json.dumps(self.dump(version_id), sort_keys=True, default=str)
        return hashlib.sha256(dumped.encode()).hexdigest()


VERSION_SCOPED: tuple[Any, ...] = (
    models.World,
    models.Character,
    models.Place,
    models.Fact,
    models.FactUsage,
    models.Event,
    models.EventCharacter,
    models.OutlineChapter,
    models.StyleSheet,
    models.Chapter,
    models.CanonCard,
)


def _of(session: Session, model: Any, version_id: int) -> list[Any]:
    """Las filas de `model` de la versión, también las que cuelgan de un hecho o un evento."""
    query = session.query(model)
    if model is models.FactUsage:
        query = query.join(models.Fact, models.Fact.id == models.FactUsage.fact_id).filter(
            models.Fact.version_id == version_id
        )
    elif model is models.EventCharacter:
        query = query.join(models.Event, models.Event.id == models.EventCharacter.event_id).filter(
            models.Event.version_id == version_id
        )
    else:
        query = query.filter(model.version_id == version_id)
    return list(query.order_by(model.id).all())


def _as_dict(row: Any) -> dict[str, Any]:
    return {attr.key: getattr(row, attr.key) for attr in inspect(type(row)).column_attrs}


def chapter_hash(title: str, text: str) -> str:
    return hashlib.sha256(f"{title}\n{text}".encode()).hexdigest()


@dataclass(frozen=True)
class V1:
    novel_id: int
    version_id: int
    characters: dict[str, int]
    places: dict[str, int]
    facts: dict[str, int]  # por valor: en V1 no se repite ninguno


@pytest.fixture
def store(session_factory: sessionmaker[Session]) -> Store:
    return Store(session_factory)


@pytest.fixture
def f1() -> ConfirmedBrief:
    return f1_brief()


@pytest.fixture
def f2() -> ConfirmedBrief:
    return f2_brief()


class InjectedFault(RuntimeError):
    """Fallo provocado por la prueba en mitad de una escritura."""


class FailingUnitOfWork:
    """Envuelve una unidad de trabajo y falla al añadir la `nth`-ésima fila de tipo `model`."""

    def __init__(self, uow: UnitOfWork, model: type, nth: int = 1) -> None:
        self.session = uow.session
        self._uow = uow
        self._model = model
        self._left = nth

    def add(self, obj: object) -> None:
        if isinstance(obj, self._model):
            self._left -= 1
            if self._left == 0:
                raise InjectedFault(f"fallo provocado al escribir {type(obj).__tablename__}")
        self._uow.add(obj)

    def delete(self, obj: object) -> None:
        self._uow.delete(obj)


@dataclass(frozen=True)
class Faults:
    error: type[InjectedFault] = InjectedFault
    wrap: type[FailingUnitOfWork] = FailingUnitOfWork


@pytest.fixture
def faults() -> Faults:
    return Faults()

"""Datos de las pruebas de la 009 (F1, F2), construidos directamente en el almacén."""

from __future__ import annotations

import datetime as dt
import itertools
from dataclasses import dataclass

import pytest
from sqlalchemy.orm import Session, sessionmaker

from story_maker.store.brief_canon import (
    BriefCloseOne,
    BriefExtractedFact,
    BriefRecipient,
    BriefRecollection,
    BriefTrait,
    ConfirmedBrief,
    create_generation_candidate,
)
from story_maker.store.models import Novel, User
from story_maker.store.session import unit_of_work

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


@pytest.fixture
def store(session_factory: sessionmaker[Session]) -> Store:
    return Store(session_factory)


@pytest.fixture
def f1() -> ConfirmedBrief:
    return f1_brief()


@pytest.fixture
def f2() -> ConfirmedBrief:
    return f2_brief()

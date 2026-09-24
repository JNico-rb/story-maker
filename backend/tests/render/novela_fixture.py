"""Fixture compartida de la 013: N con V1 (sin cambios) y V2 (Toby pasa a «Nala»; capítulos 3 y
7 reescritos) publicadas, y K, candidata sin publicar copiada de V2 (mismas convenciones que
`specs/backend/013-lectura-y-pdf.md`). Simón no tiene `UsoDeHecho` ni evento (013-C03); el bosque
solo aparece por un evento registrado, sin `UsoDeHecho` (013-C01 «por UsoDeHecho o evento»)."""

from __future__ import annotations

import datetime as dt
import hashlib
import itertools
from dataclasses import dataclass

from sqlalchemy.orm import Session, sessionmaker

from story_maker.store import models
from story_maker.store.brief_canon import (
    BriefCloseOne,
    BriefRecipient,
    BriefTrait,
    ConfirmedBrief,
    create_generation_candidate,
)
from story_maker.store.models import Brief, Novel, User
from story_maker.store.session import UnitOfWork, unit_of_work
from story_maker.store.story_bible import change_fact_value
from story_maker.store.version_copy import copy_version
from story_maker.store.versions import publish

NOW = dt.datetime(2026, 9, 24, 11, 0)
DEDICATION = "Para Ada, con todo el cariño."
TITLE = "La aventura de Ada"

_emails = itertools.count(1)


def _brief() -> ConfirmedBrief:
    return ConfirmedBrief(
        recipient=BriefRecipient(
            "Ada", 30, name_element_id=1, traits=(BriefTrait("curiosa", 2, mandatory=False),)
        ),
        close_ones=(
            BriefCloseOne("Toby", "perro", "animal", element_id=3, mandatory=True),
            BriefCloseOne("Simón", "amigo", "person", element_id=4, mandatory=False),
        ),
    )


def chapter_hash(title: str, text: str) -> str:
    return hashlib.sha256(f"{title}\n{text}".encode()).hexdigest()


def _add_chapters(uow: UnitOfWork, version_id: int) -> None:
    for n in range(1, 11):
        title, text = f"Capítulo {n}", f"Texto del capítulo {n}, con Ada."
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


@dataclass(frozen=True)
class Novela:
    novel_id: int
    owner_user_id: int
    owner_email: str
    v1_id: int
    v2_id: int
    k_id: int  # candidata sin publicar (013-C04)


def build_novela(session_factory: sessionmaker[Session]) -> Novela:
    owner_email = f"cliente-{next(_emails)}@example.com"
    with unit_of_work(session_factory) as uow:
        user = User(email=owner_email, password_hash="h", created_at=NOW)
        uow.add(user)
        uow.session.flush()
        novel = Novel(user_id=user.id, title=TITLE, embedding_model="m1", created_at=NOW)
        uow.add(novel)
        uow.session.flush()
        uow.add(Brief(novel_id=novel.id, content={"dedication": DEDICATION}, status="confirmed"))
        owner_id, novel_id = user.id, novel.id

    with unit_of_work(session_factory) as uow:
        v1_id = create_generation_candidate(uow, novel_id, _brief(), now=NOW).id

    with unit_of_work(session_factory) as uow:
        session: Session = uow.session
        ada = _character(session, v1_id, "Ada")
        toby = _character(session, v1_id, "Toby")
        forest = models.Place(
            version_id=v1_id, canonical_name="el bosque", description="un claro", origin="invented"
        )
        uow.add(forest)
        session.flush()
        event = models.Event(
            version_id=v1_id,
            statement="Ada y Toby juegan en el bosque",
            moment=dt.datetime(2026, 5, 1, 10, 0),
            place_id=forest.id,
            type="ordinary",
            analepsis=False,
            origin="recorded",
            chapter=4,
            beat=1,
        )
        uow.add(event)
        session.flush()
        uow.add(models.EventCharacter(event_id=event.id, character_id=ada.id))
        uow.add(models.EventCharacter(event_id=event.id, character_id=toby.id))

        ada_name = _name_fact(session, v1_id, ada.id)
        toby_name = _name_fact(session, v1_id, toby.id)
        for n in range(1, 11):
            uow.add(models.FactUsage(fact_id=ada_name.id, chapter=n))
        for n in (1, 3):
            uow.add(models.FactUsage(fact_id=toby_name.id, chapter=n))

        _add_chapters(uow, v1_id)

    with unit_of_work(session_factory) as uow:
        publish(uow, v1_id, pdf_path=f"v{v1_id}.pdf", now=NOW)

    with unit_of_work(session_factory) as uow:
        v2_id = copy_version(uow, v1_id, now=NOW).version.id
        toby_v2 = (
            uow.session.query(models.Fact)
            .filter_by(version_id=v2_id, attribute="name", value="Toby")
            .one()
        )
        change_fact_value(uow, toby_v2.id, "Nala")

    with unit_of_work(session_factory) as uow:
        new_text = "Texto nuevo del capítulo {n}, con Nala."
        _rewrite_chapter(uow.session, v2_id, 3, "Capítulo 3", new_text.format(n=3))
        _rewrite_chapter(uow.session, v2_id, 7, "Capítulo 7", new_text.format(n=7))

    with unit_of_work(session_factory) as uow:
        publish(uow, v2_id, pdf_path=f"v{v2_id}.pdf", now=NOW)

    with unit_of_work(session_factory) as uow:
        k_id = copy_version(uow, v2_id, now=NOW).version.id

    return Novela(novel_id, owner_id, owner_email, v1_id, v2_id, k_id)


def _character(session: Session, version_id: int, name: str) -> models.Character:
    query = session.query(models.Character)
    return query.filter_by(version_id=version_id, canonical_name=name).one()


def _name_fact(session: Session, version_id: int, character_id: int) -> models.Fact:
    return (
        session.query(models.Fact)
        .filter_by(version_id=version_id, character_id=character_id, attribute="name")
        .one()
    )


def _rewrite_chapter(session: Session, version_id: int, number: int, title: str, text: str) -> None:
    chapter = session.query(models.Chapter).filter_by(version_id=version_id, number=number).one()
    chapter.title, chapter.text = title, text
    chapter.content_hash = chapter_hash(title, text)

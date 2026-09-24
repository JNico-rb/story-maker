"""Fixtures del recuperador: base real, filas de CanonCards de fixture escritas con la unidad de
trabajo de la 001 y el doble de vectores fijos. Ningún modelo real (`verification.md` §3.3)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator
from itertools import count
from pathlib import Path

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from story_maker.retrieval.embedding import EmbeddingModel
from story_maker.retrieval.fake import FixedVectors
from story_maker.retrieval.vectors import fingerprint, store_vectors
from story_maker.store.models import (
    CanonCard,
    Chapter,
    Character,
    Event,
    Novel,
    OutlineChapter,
    Place,
    User,
    Version,
)
from story_maker.store.session import (
    create_schema,
    make_engine,
    make_session_factory,
    unit_of_work,
)

NOW = dt.datetime(2026, 9, 24, 12, 0)


class Canon:
    """Una story bible mínima por versión (personajes y lugares) y sus CanonCards."""

    def __init__(self, session_factory: sessionmaker[Session], embedder: FixedVectors) -> None:
        self.session_factory = session_factory
        self.embedder = embedder
        self.models: dict[int, str] = {}
        self._users = count(1)

    def version(self, model: str = "modelo-a") -> int:
        """Una versión candidata de una novela nueva, con `model` como modelo de la novela."""
        with unit_of_work(self.session_factory) as uow:
            user = User(
                email=f"cuenta-{next(self._users)}@example.test",
                password_hash="x",
                created_at=NOW,
            )
            uow.add(user)
            uow.session.flush()
            novel = Novel(user_id=user.id, title=None, embedding_model=model, created_at=NOW)
            uow.add(novel)
            uow.session.flush()
            version_id = self._new_version(uow.session, novel.id)
        self.models[version_id] = model
        return version_id

    def other_version(self, version_id: int) -> int:
        """Otra versión candidata de la misma novela."""
        with unit_of_work(self.session_factory) as uow:
            version = uow.session.get(Version, version_id)
            assert version is not None
            other = self._new_version(uow.session, version.novel_id)
        self.models[other] = self.models[version_id]
        return other

    def _new_version(self, session: Session, novel_id: int) -> int:
        version = Version(
            novel_id=novel_id, status="candidate", changed_chapters=[], created_at=NOW
        )
        session.add(version)
        session.flush()
        return version.id

    def character(self, version_id: int, name: str) -> int:
        with unit_of_work(self.session_factory) as uow:
            character = Character(
                version_id=version_id,
                type="invented",
                species="person",
                canonical_name=name,
                origin="invented",
            )
            uow.add(character)
            uow.session.flush()
            return character.id

    def place(self, version_id: int, name: str) -> int:
        with unit_of_work(self.session_factory) as uow:
            place = Place(
                version_id=version_id, canonical_name=name, description=name, origin="invented"
            )
            uow.add(place)
            uow.session.flush()
            return place.id

    def outline_chapter(self, version_id: int, number: int, beats: list[str]) -> None:
        """El capítulo `number` del outline, con un beat por descripción, numerados desde 1."""
        with unit_of_work(self.session_factory) as uow:
            uow.add(
                OutlineChapter(
                    version_id=version_id,
                    number=number,
                    title=f"Capítulo {number}",
                    arc_function="desarrollo",
                    beats=[
                        {"number": index, "description": description}
                        for index, description in enumerate(beats, start=1)
                    ],
                    assigned_elements=[],
                )
            )

    def planned_event(
        self, version_id: int, chapter: int, beat: int, statement: str, place: int
    ) -> None:
        with unit_of_work(self.session_factory) as uow:
            uow.add(
                Event(
                    version_id=version_id,
                    statement=statement,
                    moment=dt.date(2026, 5, 1),
                    place_id=place,
                    type="ordinary",
                    analepsis=False,
                    origin="planned",
                    chapter=chapter,
                    beat=beat,
                )
            )

    def chapter(self, version_id: int, number: int, text: str) -> None:
        with unit_of_work(self.session_factory) as uow:
            uow.add(
                Chapter(
                    version_id=version_id,
                    number=number,
                    title=f"Capítulo {number}",
                    text=text,
                    summary=text,
                    word_count=len(text.split()),
                    content_hash=fingerprint(text),
                )
            )

    def card(
        self,
        version_id: int,
        text: str,
        *,
        character: int | None = None,
        place: int | None = None,
        from_chapter: int = 1,
        embedder: EmbeddingModel | None = None,
    ) -> int:
        """Una CanonCard de la entidad dada (el mundo si no se da ninguna), con su vector."""
        if character is not None:
            entity_type = "character"
        else:
            entity_type = "place" if place is not None else "world"
        with unit_of_work(self.session_factory) as uow:
            card = CanonCard(
                version_id=version_id,
                entity_type=entity_type,
                character_id=character,
                place_id=place,
                from_chapter=from_chapter,
                text=text,
                content_hash=fingerprint(text),
            )
            uow.add(card)
            store_vectors(uow, self.models[version_id], [card], embedder or self.embedder)
            uow.session.flush()
            return card.id


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    eng = make_engine(tmp_path / "story-maker.db")
    create_schema(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Session]:
    return make_session_factory(engine)


@pytest.fixture
def embedder() -> FixedVectors:
    return FixedVectors()


@pytest.fixture
def canon(session_factory: sessionmaker[Session], embedder: FixedVectors) -> Canon:
    return Canon(session_factory, embedder)

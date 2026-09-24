"""Fixtures del recuperador: base real, story bibles y CanonCards de fixture escritas con la
unidad de trabajo de la 001 y el doble de vectores fijos. Ningún modelo real
(`verification.md` §3.3)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator, Sequence
from itertools import count
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from story_maker.retrieval.cards import sync_canon_cards
from story_maker.retrieval.embedding import EmbeddingModel
from story_maker.retrieval.fake import FixedVectors
from story_maker.retrieval.vectors import fingerprint, store_vectors
from story_maker.store.brief_canon import ConfirmedBrief, create_generation_candidate
from story_maker.store.models import (
    CanonCard,
    Chapter,
    Character,
    Event,
    EventCharacter,
    Fact,
    FactUsage,
    Novel,
    OutlineChapter,
    Place,
    User,
    Version,
    World,
)
from story_maker.store.session import (
    create_schema,
    make_engine,
    make_session_factory,
    unit_of_work,
)

NOW = dt.datetime(2026, 9, 24, 12, 0)
MOMENT = dt.datetime(2026, 5, 1, 12, 0)

# Una story bible generada: por entidad, su tipo y su cadena de (desde_capitulo, texto).
Story = list[tuple[str, list[tuple[int, str]]]]


class Canon:
    """Story bibles de fixture por versión y sus CanonCards."""

    def __init__(self, session_factory: sessionmaker[Session], embedder: FixedVectors) -> None:
        self.session_factory = session_factory
        self.embedder = embedder
        self._users = count(1)

    # --- Novelas y versiones ---------------------------------------------------------------

    def version(self, model: str = "modelo-a") -> int:
        """Una versión candidata de una novela nueva, con `model` como modelo de la novela."""
        with unit_of_work(self.session_factory) as uow:
            return self._new_version(uow.session, self._novel(uow.session, model))

    def candidate(self, brief: ConfirmedBrief, model: str = "modelo-a") -> int:
        """La candidata de generación de una novela nueva, con el canon del brief (009)."""
        with unit_of_work(self.session_factory) as uow:
            novel_id = self._novel(uow.session, model)
            return create_generation_candidate(uow, novel_id, brief, now=NOW).id

    def other_version(self, version_id: int) -> int:
        """Otra versión candidata de la misma novela."""
        with unit_of_work(self.session_factory) as uow:
            version = uow.session.get(Version, version_id)
            assert version is not None
            return self._new_version(uow.session, version.novel_id)

    def _novel(self, session: Session, model: str) -> int:
        user = User(
            email=f"cuenta-{next(self._users)}@example.test", password_hash="x", created_at=NOW
        )
        session.add(user)
        session.flush()
        novel = Novel(user_id=user.id, title=None, embedding_model=model, created_at=NOW)
        session.add(novel)
        session.flush()
        return novel.id

    def _new_version(self, session: Session, novel_id: int) -> int:
        version = Version(
            novel_id=novel_id, status="candidate", changed_chapters=[], created_at=NOW
        )
        session.add(version)
        session.flush()
        return version.id

    # --- Story bible -----------------------------------------------------------------------

    def _add(self, row: Any) -> int:
        with unit_of_work(self.session_factory) as uow:
            uow.add(row)
            uow.session.flush()
            return int(row.id)

    def character(
        self,
        version_id: int,
        name: str,
        *,
        type: str = "invented",
        species: str = "person",
        origin: str = "invented",
        birth_date: dt.date | None = None,
    ) -> int:
        return self._add(
            Character(
                version_id=version_id,
                type=type,
                species=species,
                canonical_name=name,
                birth_date=birth_date,
                origin=origin,
            )
        )

    def place(
        self, version_id: int, name: str, description: str | None = None, origin: str = "invented"
    ) -> int:
        return self._add(
            Place(
                version_id=version_id,
                canonical_name=name,
                description=name if description is None else description,
                origin=origin,
            )
        )

    def world(
        self,
        version_id: int,
        description: str = "Las máquinas aprendieron a soñar.",
        consequences: Sequence[str] = ("Nadie duerme solo.", "Los sueños se comparten."),
    ) -> int:
        return self._add(
            World(
                version_id=version_id,
                novum_description=description,
                novum_scope="technological",
                novum_date=dt.date(2021, 5, 1),
                consequences=list(consequences),
            )
        )

    def fact(
        self,
        version_id: int,
        attribute: str,
        value: str,
        *,
        character: int | None = None,
        place: int | None = None,
        origin: str = "invented",
    ) -> int:
        """Un hecho del personaje, del lugar o, sin ninguno de los dos, del mundo."""
        if character is not None:
            subject = "character"
        else:
            subject = "place" if place is not None else "world"
        return self._add(
            Fact(
                version_id=version_id,
                subject_type=subject,
                character_id=character,
                place_id=place,
                attribute=attribute,
                value=value,
                origin=origin,
                mandatory=False,
            )
        )

    def usage(self, fact: int, chapter: int) -> None:
        self._add(FactUsage(fact_id=fact, chapter=chapter))

    def event(
        self,
        version_id: int,
        statement: str,
        place: int,
        *,
        origin: str,
        chapter: int | None = None,
        beat: int | None = None,
        present: Sequence[int] = (),
        excluded: int | None = None,
        moment: dt.datetime = MOMENT,
    ) -> int:
        with unit_of_work(self.session_factory) as uow:
            event = Event(
                version_id=version_id,
                statement=statement,
                moment=moment,
                place_id=place,
                type="exclusion" if excluded is not None else "ordinary",
                excluded_character_id=excluded,
                analepsis=False,
                origin=origin,
                chapter=chapter,
                beat=beat,
            )
            uow.add(event)
            uow.session.flush()
            for character in present:
                uow.add(EventCharacter(event_id=event.id, character_id=character))
            return event.id

    def planned_event(
        self, version_id: int, chapter: int, beat: int, statement: str, place: int
    ) -> None:
        self.event(version_id, statement, place, origin="planned", chapter=chapter, beat=beat)

    def outline_chapter(
        self, version_id: int, number: int, beats: Sequence[str | dict[str, Any]]
    ) -> None:
        """El capítulo `number` del outline, con sus beats numerados desde 1. Un beat es su
        descripción o un objeto con `description`, `characters` (ids) y `facts_used` (ids)."""
        stored = []
        for index, beat in enumerate(beats, start=1):
            fields = {"description": beat} if isinstance(beat, str) else beat
            stored.append({"number": index, "characters": [], "facts_used": [], **fields})
        self._add(
            OutlineChapter(
                version_id=version_id,
                number=number,
                title=f"Capítulo {number}",
                arc_function="desarrollo",
                beats=stored,
                assigned_elements=[],
            )
        )

    def chapter(self, version_id: int, number: int, text: str, summary: str | None = None) -> None:
        self._add(
            Chapter(
                version_id=version_id,
                number=number,
                title=f"Capítulo {number}",
                text=text,
                summary=text if summary is None else summary,
                word_count=len(text.split()),
                content_hash=fingerprint(text),
            )
        )

    def named(self, version_id: int, name: str) -> tuple[int | None, int | None]:
        """(character_id, place_id) de la entidad de la versión con ese nombre canónico."""
        with self.session_factory() as session:
            character = (
                session.query(Character)
                .filter(Character.version_id == version_id, Character.canonical_name == name)
                .one_or_none()
            )
            if character is not None:
                return character.id, None
            place = (
                session.query(Place)
                .filter(Place.version_id == version_id, Place.canonical_name == name)
                .one()
            )
            return None, place.id

    # --- CanonCards ------------------------------------------------------------------------

    def sync(self, version_id: int, embedder: EmbeddingModel | None = None) -> None:
        """Sincroniza las CanonCards de la versión en una transacción de fixture."""
        with unit_of_work(self.session_factory) as uow:
            sync_canon_cards(uow, version_id, embedder or self.embedder)

    def cards(self, version_id: int) -> list[CanonCard]:
        with self.session_factory() as session:
            return list(
                session.query(CanonCard)
                .filter(CanonCard.version_id == version_id)
                .order_by(CanonCard.entity_type, CanonCard.from_chapter, CanonCard.id)
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
            store_vectors(uow, [card], embedder or self.embedder)
            uow.session.flush()
            return card.id

    def story(
        self, version_id: int, entities: Story, embedder: EmbeddingModel | None = None
    ) -> dict[int, tuple[int, int]]:
        """Las entidades de `entities` y sus cadenas de tarjetas, en una unidad de trabajo.
        Devuelve tarjeta → (índice de la entidad, `desde_capitulo`)."""
        with unit_of_work(self.session_factory) as uow:
            placed: list[tuple[CanonCard, int, int]] = []
            for index, (kind, chain) in enumerate(entities):
                character = place = None
                if kind == "character":
                    row: Character | Place = Character(
                        version_id=version_id,
                        type="invented",
                        species="person",
                        canonical_name=f"Personaje {index}",
                        origin="invented",
                    )
                elif kind == "place":
                    row = Place(
                        version_id=version_id,
                        canonical_name=f"Lugar {index}",
                        description=f"Lugar {index}",
                        origin="invented",
                    )
                if kind != "world":
                    uow.add(row)
                    uow.session.flush()
                    character = row.id if kind == "character" else None
                    place = row.id if kind == "place" else None
                for from_chapter, text in chain:
                    card = CanonCard(
                        version_id=version_id,
                        entity_type=kind,
                        character_id=character,
                        place_id=place,
                        from_chapter=from_chapter,
                        text=text,
                        content_hash=fingerprint(text),
                    )
                    uow.add(card)
                    placed.append((card, index, from_chapter))
            store_vectors(uow, [card for card, _, _ in placed], embedder or self.embedder)
            uow.session.flush()
            return {card.id: (index, chapter) for card, index, chapter in placed}


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

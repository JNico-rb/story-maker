"""Copia de versión (009-C11 a 009-C14, 009-I4, 009-I2).

`store` es el atajo de `conftest.py` sobre el almacén de la prueba (tipo `Store`)."""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import text

from story_maker.store import models
from story_maker.store.session import unit_of_work

TABLES = (
    "worlds",
    "characters",
    "places",
    "facts",
    "fact_usages",
    "events",
    "event_characters",
    "outline_chapters",
    "style_sheets",
    "chapters",
    "canon_cards",
)
REFERENCES = {
    "facts": {"character_id": "characters", "place_id": "places"},
    "fact_usages": {"fact_id": "facts"},
    "events": {"place_id": "places", "excluded_character_id": "characters"},
    "event_characters": {"event_id": "events", "character_id": "characters"},
    "canon_cards": {"character_id": "characters", "place_id": "places"},
}


def _translated(row: dict[str, Any], table: str, ids: dict[str, dict[int, int]]) -> dict[str, Any]:
    """La fila de la base tal como debe quedar en la copia: su id y sus referencias traducidos."""
    out = {k: v for k, v in row.items() if k != "version_id"}
    out["id"] = ids[table][row["id"]]
    for column, target in REFERENCES.get(table, {}).items():
        if out[column] is not None:
            out[column] = ids[target][out[column]]
    return out


def _without_version(row: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in row.items() if k != "version_id"}


def _cards_matching(store: Any, word: str, version_id: int) -> set[int]:
    with store.session() as session:
        rows = session.execute(
            text(
                "SELECT c.id FROM canon_cards_fts "
                "JOIN canon_cards c ON c.id = canon_cards_fts.rowid "
                "WHERE canon_cards_fts MATCH :word AND c.version_id = :version"
            ),
            {"word": word, "version": version_id},
        )
        return {r[0] for r in rows}


def test_the_copy_reproduces_the_whole_base_with_new_ids(store: Any) -> None:
    v1 = store.build_v1()

    k_id, ids = store.copy(v1.version_id)

    base, copy = store.dump(v1.version_id), store.dump(k_id)
    k = copy["versions"][0]
    assert (
        k["status"],
        k["base_version_id"],
        k["number"],
        k["changed_chapters"],
        k["pdf_path"],
    ) == (
        "candidate",
        v1.version_id,
        None,
        [],
        None,
    )
    for table in TABLES:
        assert base[table], table  # V1 tiene filas en cada tabla de ámbito versión
        assert set(ids[table]) == {r["id"] for r in base[table]}, table
        assert set(ids[table].values()) == {r["id"] for r in copy[table]}, table
        expected = sorted((_translated(r, table, ids) for r in base[table]), key=lambda r: r["id"])
        assert [_without_version(r) for r in copy[table]] == expected, table
    for table in ("characters", "places", "facts", "events"):
        assert not set(ids[table]) & set(ids[table].values()), table
    for table, columns in REFERENCES.items():
        for row in copy[table]:
            for column, target in columns.items():
                if row[column] is not None:
                    assert row[column] in ids[target].values(), (table, column)

    in_v1 = _cards_matching(store, "feria", v1.version_id)
    assert in_v1
    assert _cards_matching(store, "feria", k_id) == {ids["canon_cards"][c] for c in in_v1}


def test_the_copy_does_not_embed_again_it_shares_the_vectors(store: Any) -> None:
    v1 = store.build_v1()
    with store.session() as session:
        vectors_before = session.query(models.Embedding).count()

    k_id, _ = store.copy(v1.version_id)

    with store.session() as session:
        assert session.query(models.Embedding).count() == vectors_before
        novel = session.get(models.Novel, v1.novel_id)
        cards = session.query(models.CanonCard).filter_by(version_id=k_id).all()
        assert cards
        for card in cards:
            vector = (
                session.query(models.Embedding)
                .filter_by(content_hash=card.content_hash, model=novel.embedding_model)
                .one_or_none()
            )
            assert vector is not None, card.text


def test_the_base_does_not_change_when_copied_nor_while_the_candidate_is_worked(
    store: Any,
) -> None:
    v1 = store.build_v1()
    before = store.fingerprint(v1.version_id)

    k_id, ids = store.copy(v1.version_id)
    assert store.fingerprint(v1.version_id) == before

    def in_k(change: Any) -> None:
        with unit_of_work(store.session_factory) as uow:
            change(uow.session, uow)
        assert store.fingerprint(v1.version_id) == before

    def change_a_fact(session: Any, _uow: Any) -> None:
        session.get(models.Fact, ids["facts"][v1.facts["la paella"]]).value = "el cocido"

    def rewrite_chapter_3(session: Any, _uow: Any) -> None:
        chapter = session.query(models.Chapter).filter_by(version_id=k_id, number=3).one()
        chapter.text = "Otro texto del capítulo 3."
        chapter.content_hash = "otra-huella"

    def delete_a_fact_usage(session: Any, uow: Any) -> None:
        fact_id = ids["facts"][v1.facts["Toby"]]
        uow.delete(session.query(models.FactUsage).filter_by(fact_id=fact_id, chapter=7).one())

    def add_a_recorded_event(session: Any, uow: Any) -> None:
        uow.add(
            models.Event(
                version_id=k_id,
                statement="E6: nuevo",
                moment=dt.datetime(2026, 5, 13, 9, 0),
                place_id=ids["places"][v1.places["la estación"]],
                type="ordinary",
                analepsis=False,
                origin="recorded",
                chapter=3,
                beat=2,
            )
        )

    def publish_as_v2(session: Any, _uow: Any) -> None:
        k = session.get(models.Version, k_id)
        k.status, k.number, k.published_at = "published", 2, store.now

    for change in (
        change_a_fact,
        rewrite_chapter_3,
        delete_a_fact_usage,
        add_a_recorded_event,
        publish_as_v2,
    ):
        in_k(change)
    assert store.fingerprint(k_id) != before

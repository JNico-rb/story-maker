"""Copia de versión (009-C11 a 009-C14, 009-I4, 009-I2).

`store` es el atajo de `conftest.py` sobre el almacén de la prueba (tipo `Store`)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

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

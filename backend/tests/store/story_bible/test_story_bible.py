"""Cambio de un hecho en la candidata (009-C15, 009-C16, 009-I6).

`store` es el atajo de `conftest.py` sobre el almacén de la prueba (tipo `Store`)."""

from __future__ import annotations

from typing import Any

from story_maker.store import models


def _fact(store: Any, fact_id: int) -> Any:
    with store.session() as session:
        return session.get(models.Fact, fact_id)


def _usages(store: Any, fact_id: int) -> list[int]:
    with store.session() as session:
        rows = session.query(models.FactUsage).filter_by(fact_id=fact_id).all()
        return sorted(u.chapter for u in rows)


def test_changing_the_value_of_a_fact_of_the_candidate(store: Any) -> None:
    v1 = store.build_v1()
    k_id, ids = store.copy(v1.version_id)
    x1_in_k = ids["facts"][v1.facts["la paella"]]
    before = _fact(store, x1_in_k)

    store.change_fact(x1_in_k, "el cocido")

    after = _fact(store, x1_in_k)
    assert after.value == "el cocido"
    kept = ("id", "version_id", "subject_type", "character_id", "attribute", "origin", "mandatory")
    for column in (*kept, "personal_element_id"):
        assert getattr(after, column) == getattr(before, column), column
    assert (after.origin, after.mandatory, after.personal_element_id) == ("free_text", True, 10)
    assert _usages(store, x1_in_k) == [5]
    assert _fact(store, v1.facts["la paella"]).value == "la paella"
    assert store.foreign_references(k_id) == []

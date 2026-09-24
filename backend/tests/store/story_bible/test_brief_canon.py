"""Canon del brief en la candidata de generación (009-C01 a 009-C10, 009-I7).

`store` es el atajo de `conftest.py` sobre el almacén de la prueba (tipo `Store`)."""

from __future__ import annotations

from typing import Any

from story_maker.store import models
from story_maker.store.brief_canon import ConfirmedBrief

from_brief = "brief"


def _rows(store: Any, model: Any, version_id: int) -> list[Any]:
    with store.session() as session:
        return list(session.query(model).filter(model.version_id == version_id).all())


def test_the_generation_candidate_is_born_with_the_brief_canon(
    store: Any, f1: ConfirmedBrief
) -> None:
    novel_id = store.new_novel()

    version_id = store.generation(novel_id, f1)

    with store.session() as session:
        versions = session.query(models.Version).filter_by(novel_id=novel_id).all()
    assert [v.id for v in versions] == [version_id]
    version = versions[0]
    assert version.status == "candidate"
    assert version.base_version_id is None
    assert version.number is None
    assert version.changed_chapters == []
    assert version.pdf_path is None
    assert version.created_at == store.now

    characters = _rows(store, models.Character, version_id)
    places = _rows(store, models.Place, version_id)
    facts = _rows(store, models.Fact, version_id)
    events = _rows(store, models.Event, version_id)
    assert (len(characters), len(places), len(facts), len(events)) == (4, 3, 13, 3)
    assert {c.origin for c in characters} == {from_brief}
    assert {p.origin for p in places} == {from_brief}
    assert {e.origin for e in events} == {from_brief}
    assert sorted(f.origin for f in facts) == ["brief"] * 12 + ["free_text"]
    assert [f.value for f in facts if f.origin == "free_text"] == ["la paella"]

    for model in (
        models.World,
        models.OutlineChapter,
        models.StyleSheet,
        models.Chapter,
        models.CanonCard,
    ):
        assert _rows(store, model, version_id) == [], model.__tablename__
    with store.session() as session:
        usages = (
            session.query(models.FactUsage)
            .join(models.Fact, models.Fact.id == models.FactUsage.fact_id)
            .filter(models.Fact.version_id == version_id)
            .all()
        )
    assert usages == []

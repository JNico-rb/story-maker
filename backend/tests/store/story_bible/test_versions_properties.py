"""009-I5: la historia de versiones es lineal (prueba basada en propiedades, `verification.md`
§3.4): secuencias al azar de crear la de generación, copiar la vigente, publicar y descartar."""

from __future__ import annotations

from typing import Any

from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from story_maker.store import models
from story_maker.store.versions import VersionTransitionRejected

operations = st.lists(
    st.tuples(
        st.sampled_from(
            ["generation", "copy_current", "copy_current", "publish", "publish", "discard"]
        ),
        st.integers(min_value=0, max_value=5),
    ),
    min_size=1,
    max_size=12,
)


@settings(
    max_examples=60,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(sequence=operations)
# Dos copias de la misma base publicadas una tras otra: la segunda ya no parte de la vigente.
@example(
    sequence=[
        ("generation", 0),
        ("publish", 0),
        ("copy_current", 0),
        ("copy_current", 0),
        ("publish", 0),
        ("publish", 0),
    ]
)
def test_the_version_history_is_linear(store: Any, f1: Any, sequence: Any) -> None:
    novel_id = store.new_novel()
    published: list[int] = []  # en orden de publicación

    for operation, pick in sequence:
        with store.session() as session:
            candidates = [
                v.id
                for v in session.query(models.Version)
                .filter_by(novel_id=novel_id, status="candidate")
                .order_by(models.Version.id)
            ]
        chosen = candidates[pick % len(candidates)] if candidates else None
        try:
            if operation == "generation":
                store.generation(novel_id, f1)
            elif operation == "copy_current" and store.current(novel_id) is not None:
                store.copy(store.current(novel_id))
            elif operation == "publish" and chosen is not None:
                store.publish(chosen)
                published.append(chosen)
            elif operation == "discard" and chosen is not None:
                store.discard(chosen)
        except VersionTransitionRejected:
            pass

    with store.session() as session:
        versions = {v.id: v for v in session.query(models.Version).filter_by(novel_id=novel_id)}
    assert [versions[v].number for v in published] == list(range(1, len(published) + 1))
    for previous, version_id in zip([None, *published], published, strict=False):
        assert versions[version_id].base_version_id == previous
    assert store.current(novel_id) == (published[-1] if published else None)
    for version in versions.values():
        if version.status != "published":
            assert version.number is None
    assert {v.id for v in versions.values() if v.status == "published"} == set(published)

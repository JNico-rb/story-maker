"""Estados de las versiones (009-C17 a 009-C22, 009-I1, 009-I5).

`store` es el atajo de `conftest.py` sobre el almacén de la prueba (tipo `Store`)."""

from __future__ import annotations

from typing import Any

import pytest

from story_maker.store.versions import VersionTransitionRejected


def test_publishing_the_first_version(store: Any, f1: Any) -> None:
    novel_id = store.new_novel()
    g_id = store.generation(novel_id, f1)
    store.add_chapters(g_id)
    assert store.current(novel_id) is None

    store.publish(g_id, pdf_path="pdfs/n1-v1.pdf")

    g = store.version(g_id)
    assert (g.status, g.number, g.published_at, g.changed_chapters, g.pdf_path) == (
        "published",
        1,
        store.now,
        [],
        "pdfs/n1-v1.pdf",
    )
    assert store.current(novel_id) == g_id


def test_publishing_a_copy_gives_the_next_number_and_the_chapters_changed_by_hash(
    store: Any,
) -> None:
    v1 = store.build_v1()
    k_id, _ = store.copy(v1.version_id)
    store.rewrite_chapter(k_id, 3, "Capítulo 3", "Otro texto del capítulo 3.")
    store.rewrite_chapter(k_id, 7, "Otro título", "Texto del capítulo 7, con Marta.")
    store.rewrite_chapter(k_id, 5, "Capítulo 5", "Texto del capítulo 5, con Marta.")
    v1_before = store.fingerprint(v1.version_id)

    store.publish(k_id)

    k = store.version(k_id)
    assert (k.status, k.number, k.changed_chapters) == ("published", 2, [3, 7])
    assert store.version(v1.version_id).status == "published"
    assert store.fingerprint(v1.version_id) == v1_before
    assert store.current(v1.novel_id) == k_id


def test_discarding_a_candidate(store: Any) -> None:
    v2 = store.build_v2()
    novel_id = v2.v1.novel_id
    k3_id, _ = store.copy(v2.version_id)

    store.discard(k3_id)

    k3 = store.version(k3_id)
    assert (k3.status, k3.number) == ("discarded", None)
    assert store.current(novel_id) == v2.version_id

    next_id, _ = store.copy(v2.version_id)
    store.publish(next_id)
    assert store.version(next_id).number == 3


def test_transitions_that_do_not_start_from_a_valid_candidate_are_rejected(
    store: Any, f1: Any
) -> None:
    v2 = store.build_v2()
    novel_id, v2_id = v2.v1.novel_id, v2.version_id
    k3_id, _ = store.copy(v2_id)
    store.discard(k3_id)
    k2_id, _ = store.copy(v2.v1.version_id)
    generation_id = store.generation(novel_id, f1)
    cases = [
        (store.publish, v2_id, "ya está publicada"),
        (store.discard, v2_id, "está publicada"),
        (store.publish, k3_id, "está descartada"),
        (store.discard, k3_id, "está descartada"),
        (store.publish, k2_id, "su versión base no es la vigente"),
        (store.publish, generation_id, "ya hay una versión publicada"),
    ]
    all_versions = [v2.v1.version_id, v2_id, k3_id, k2_id, generation_id]
    fingerprints = {v: store.fingerprint(v) for v in all_versions}

    for operation, version_id, reason in cases:
        with pytest.raises(VersionTransitionRejected) as rejected:
            operation(version_id)
        assert f"versión {version_id}" in str(rejected.value), reason
        assert reason in str(rejected.value)

    assert {v: store.fingerprint(v) for v in all_versions} == fingerprints
    assert store.version(k2_id).status == "candidate"
    assert store.version(generation_id).status == "candidate"
    assert store.current(novel_id) == v2_id


def test_the_current_version_is_the_published_one_with_the_highest_number(
    store: Any, f1: Any
) -> None:
    n2 = store.new_novel()
    store.generation(n2, f1)

    v2 = store.build_v2()
    n1 = v2.v1.novel_id
    store.copy(v2.version_id)  # una candidata abierta
    k3_id, _ = store.copy(v2.version_id)
    store.discard(k3_id)

    n3 = store.new_novel()
    latest = store.generation(n3, f1)
    store.publish(latest)
    for _ in range(3):
        latest, _ = store.copy(latest)
        store.publish(latest)

    assert store.current(n2) is None
    assert store.current(n1) == v2.version_id
    assert store.current(n3) == latest
    assert store.version(latest).number == 4
    assert store.version(v2.version_id).number == 2

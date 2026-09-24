"""Estados de las versiones (009-C17 a 009-C22, 009-I1, 009-I5).

`store` es el atajo de `conftest.py` sobre el almacén de la prueba (tipo `Store`)."""

from __future__ import annotations

from typing import Any


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

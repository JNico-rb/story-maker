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

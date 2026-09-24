"""Verificación de 012-C26 contra `CatalogoDeTropos`: ya construido en 010
(`src/story_maker/domain/trope_catalog.py`), lo posee 012 (`architecture.md` §18, «Quién crea el
CatalogoDeTropos»). No se repite código: `tests/domain/test_trope_catalog.py` (010) ya cubre
nombre, marcador y origen curado de cada tropo; aquí solo lo que 012-C26 añade."""

from __future__ import annotations

from story_maker.domain.trope_catalog import TROPE_CATALOG


def test_the_catalog_has_no_repeated_names() -> None:
    names = [trope.name for trope in TROPE_CATALOG]

    assert len(names) == len(set(names))

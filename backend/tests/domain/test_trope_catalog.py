"""`CatalogoDeTropos` curado (010-C07; `domain-knowledge.md` §6, `definitions.md` §6)."""

from __future__ import annotations

from story_maker.domain.trope_catalog import TROPE_CATALOG

EXPECTED_NAMES = {
    "singularidad redentora o apocalíptica",
    "rebelión de las máquinas",
    "ia que desarrolla conciencia o descubre el amor",
    "último humano con empleo",
    "renta básica distópica",
    "vigilancia total",
    "dilema del tranvía algorítmico",
}


def test_the_catalog_contains_at_least_the_seven_genre_tropes() -> None:
    names = {trope.name.lower() for trope in TROPE_CATALOG}

    assert names >= EXPECTED_NAMES


def test_every_trope_has_a_name_at_least_one_marker_and_a_curated_origin() -> None:
    assert len(TROPE_CATALOG) >= 7
    for trope in TROPE_CATALOG:
        assert trope.name
        assert len(trope.markers) >= 1
        assert all(marker for marker in trope.markers)
        assert trope.origin == "curated"

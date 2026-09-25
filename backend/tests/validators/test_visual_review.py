"""`revision-visual`: la comparación entre lo observado y lo esperado (017-C04 a 017-C09,
017-C13, 017-I1, 017-I4), sin base de datos ni sesión."""

from __future__ import annotations

import dataclasses
from collections.abc import Callable
from typing import Any

import pytest
from tests.pipeline.gate.visual import (
    DEDICATION,
    EMPTY,
    EXPECTED,
    TITLE,
    chapter_text,
    faithful,
    first_sentence,
)

from story_maker.validators.visual_review import (
    PARTS,
    ExpectedStructure,
    VisualReviewSubmission,
    VisualVerdict,
    compare,
    sentence_in,
    texts_match,
)


def verdict_of(delivery: dict[str, Any]) -> VisualVerdict:
    return compare(EXPECTED, VisualReviewSubmission.model_validate(delivery))


# --- 017-C04 -------------------------------------------------------------------------------------


def test_a_review_that_observes_exactly_the_expected_passes_in_the_four_parts() -> None:
    verdict = verdict_of(faithful())

    assert verdict.passed
    assert verdict.parts == tuple((part, True) for part in PARTS)
    assert verdict.defects == ()


# --- 017-C05 -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("observed", "expected", "match"),
    [
        ("MARTA", "Marta", True),
        ("Para  Marta,\ncon cariño", "Para Marta, con cariño", True),
        ("Martha", "Marta", False),
        ("Márta", "Marta", False),
        ("Para Marta con cariño", "Para Marta, con cariño", False),
    ],
)
def test_two_texts_match_ignoring_spaces_and_case_but_never_letters_accents_or_signs(
    observed: str, expected: str, match: bool
) -> None:
    assert texts_match(observed, expected) is match


@pytest.mark.parametrize(
    ("observed", "match"),
    [(first_sentence(3), True), (first_sentence(4), False), ("", False)],
)
def test_a_first_sentence_matches_only_if_it_is_in_the_text_of_its_chapter(
    observed: str, match: bool
) -> None:
    assert sentence_in(observed, chapter_text(3)) is match


# --- 017-C06 -------------------------------------------------------------------------------------

RENAMED = dataclasses.replace(
    EXPECTED, cover=dataclasses.replace(EXPECTED.cover, recipient="Lucía")
)


def with_cover(**cover: str) -> dict[str, Any]:
    delivery = faithful()
    delivery["portada"] = {**delivery["portada"], **cover}
    return delivery


@pytest.mark.parametrize(
    ("expected", "delivery", "shown"),
    [
        (EXPECTED, with_cover(dedication=""), DEDICATION),
        (EXPECTED, with_cover(dedication="Para Andrés, que siempre vuelve"), DEDICATION),
        (EXPECTED, with_cover(title=""), TITLE),
        (RENAMED, with_cover(recipient="Marta"), "Lucía"),
    ],
    ids=["sin-dedicatoria", "dedicatoria-ajena", "sin-titulo", "destinatario-antiguo"],
)
def test_a_cover_that_does_not_show_its_own_is_a_render_failure_and_the_rest_is_still_evaluated(
    expected: ExpectedStructure, delivery: dict[str, Any], shown: str
) -> None:
    verdict = compare(expected, VisualReviewSubmission.model_validate(delivery))

    [defect] = verdict.defects
    assert (defect.part, defect.kind, defect.chapter) == ("portada", "render", None)
    assert shown in defect.message
    assert "se vio" in defect.message
    assert verdict.parts == (
        ("portada", False),
        ("indice", True),
        ("capitulos", True),
        ("ficha", True),
    )


# --- 017-C07 -------------------------------------------------------------------------------------


def with_index(destinations: list[str | None]) -> dict[str, Any]:
    delivery = faithful()
    delivery["indice"] = [
        {"text": f"entrada {i}", "destination": d} for i, d in enumerate(destinations, 1)
    ]
    return delivery


def to(*chapters: int) -> list[str | None]:
    return [f"capitulo-{n}" for n in chapters]


@pytest.mark.parametrize(
    ("destinations", "defects"),
    [
        (to(*range(1, 10)), 1),
        (to(*range(1, 12)), 1),
        (to(1, 2, 3, 5, 5, 6, 7, 8, 9, 10), 1),
        ([*to(1, 2, 3, 4, 5, 6), None, *to(8, 9, 10)], 1),
        (to(1, 3, 2, 4, 5, 6, 7, 8, 9, 10), 2),
    ],
    ids=["9-entradas", "11-entradas", "4a-al-5", "7a-sin-destino", "2-y-3-invertidas"],
)
def test_an_index_that_does_not_lead_to_its_chapters_is_a_render_failure_per_discrepancy(
    destinations: list[str | None], defects: int
) -> None:
    verdict = verdict_of(with_index(destinations))

    assert len(verdict.defects) == defects
    assert {(d.part, d.kind, d.chapter) for d in verdict.defects} == {("indice", "render", None)}
    assert dict(verdict.parts)["indice"] is False


def test_an_index_of_ten_entries_leading_to_one_to_ten_in_order_passes() -> None:
    verdict = verdict_of(with_index(to(*range(1, 11))))

    assert dict(verdict.parts)["indice"] is True
    assert verdict.defects == ()


# --- 017-C08 -------------------------------------------------------------------------------------


def with_chapters(edit: Callable[[list[dict[str, Any]]], list[dict[str, Any]]]) -> dict[str, Any]:
    delivery = faithful()
    delivery["capitulos"] = edit(delivery["capitulos"])
    return delivery


def _retitle_3(chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**c, "title": "Otro título"} if c["number"] == 3 else c for c in chapters]


def _no_sentence_8(chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**c, "first_sentence": ""} if c["number"] == 8 else c for c in chapters]


@pytest.mark.parametrize(
    ("edit", "chapter"),
    [
        (lambda cs: [c for c in cs if c["number"] != 6], 6),
        (_retitle_3, 3),
        (_no_sentence_8, 8),
        (lambda cs: [*cs, {"number": 11, "title": "Epílogo", "first_sentence": "Fin."}], 11),
    ],
    ids=["sin-el-6", "titulo-del-3", "8-sin-frase", "capitulo-11"],
)
def test_a_chapter_not_seen_whole_is_a_render_failure_naming_it_without_attributing_it(
    edit: Callable[[list[dict[str, Any]]], list[dict[str, Any]]], chapter: int
) -> None:
    verdict = verdict_of(with_chapters(edit))

    [defect] = verdict.defects
    assert (defect.part, defect.kind, defect.chapter) == ("capitulos", "render", None)
    assert f"capítulo {chapter}" in defect.message
    assert dict(verdict.parts)["capitulos"] is False


# --- 017-C09 -------------------------------------------------------------------------------------


def with_entity(name: str, links: list[str | None] | None) -> dict[str, Any]:
    """La entrega fiel con la entidad `name` quitada (`links` None) o con esos enlaces."""
    delivery = faithful()
    ficha = [e for e in delivery["ficha"] if e["name"] != name]
    if links is not None:
        ficha.append({"name": name, "links": [{"destination": d} for d in links]})
    delivery["ficha"] = ficha
    return delivery


@pytest.mark.parametrize(
    ("delivery", "entity"),
    [
        (with_entity("Villaverde", None), "Villaverde"),
        (with_entity("Toby", to(2)), "Toby"),
        (with_entity("Toby", to(3, 5)), "Toby"),
        (with_entity("Toby", to(2, 5, 7)), "Toby"),
        (with_entity("Toby", [*to(2, 5), None]), "Toby"),
        (with_entity("Nala", to(2)), "Nala"),
    ],
    ids=["sin-villaverde", "toby-sin-el-5", "toby-al-3", "toby-de-mas", "sin-destino", "ajena"],
)
def test_a_ficha_that_does_not_link_what_it_should_is_a_render_failure_naming_the_entity(
    delivery: dict[str, Any], entity: str
) -> None:
    verdict = verdict_of(delivery)

    [defect] = verdict.defects
    assert (defect.part, defect.kind, defect.chapter) == ("ficha", "render", None)
    assert f"«{entity}»" in defect.message
    assert dict(verdict.parts)["ficha"] is False


def test_a_ficha_with_every_entity_and_exactly_its_link_destinations_passes() -> None:
    delivery = with_entity("Toby", to(5, 2))

    verdict = verdict_of(delivery)

    assert dict(verdict.parts)["ficha"] is True
    assert verdict.defects == ()


# --- 017-C13 -------------------------------------------------------------------------------------


def test_an_empty_or_error_view_is_a_render_failure_in_the_four_parts() -> None:
    verdict = verdict_of(EMPTY)

    assert verdict.parts == tuple((part, False) for part in PARTS)
    assert {d.part for d in verdict.defects} == set(PARTS)
    assert {(d.kind, d.chapter) for d in verdict.defects} == {("render", None)}

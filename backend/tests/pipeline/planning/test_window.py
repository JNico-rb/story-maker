"""Ventana del planner en modo `plan` (010-C06).

El brief y la story bible inicial son los del brief de referencia de
`specs/backend/010-planificacion.md`; se construyen a mano en la prueba, como el resto de
`pipeline/planning/` mientras la 009 no esté en V2 (no leen ni escriben SQLite)."""

from __future__ import annotations

import datetime as dt
import json

from story_maker.domain.trope_catalog import TROPE_CATALOG
from story_maker.pipeline.planning.brief_view import (
    BannedEntryView,
    BriefView,
    CloseOneView,
    ExtractedFactView,
    RecipientView,
    RecollectionView,
    TraitView,
)
from story_maker.pipeline.planning.session import submit_plan_tool
from story_maker.pipeline.planning.story_bible_view import (
    EventRef,
    FactRef,
    PersonalElement,
    StoryBibleView,
)
from story_maker.pipeline.planning.window import build_planner_window
from story_maker.validators.outline import OutlineDefect

BRIEF = BriefView(
    recipient=RecipientView(
        name="Marta",
        age=40,
        traits=(
            TraitView("curiosa", mandatory=False),
            TraitView("le encanta el mar", mandatory=True),
        ),
    ),
    close_ones=(
        CloseOneView("Toby", "su perro", "animal", mandatory=True),
        CloseOneView("Rosa", "su abuela", "person", mandatory=False),
    ),
    recollections=(
        RecollectionView(
            "se perdió en la feria de su pueblo", "la feria del pueblo", ("Rosa",), None, True
        ),
        RecollectionView(
            "Rosa se fue a vivir para siempre a otro país",
            "el aeropuerto",
            ("Rosa",),
            "Rosa",
            False,
        ),
        RecollectionView(
            "llevó a Toby a la feria del pueblo", "la feria del pueblo", ("Toby",), None, False
        ),
    ),
    occasion="cumpleaños",
    genre="aventura",
    tone="tierno",
    extension="media",
    dedication="Para Marta, con cariño.",
    banned_novel=(
        BannedEntryView("Julián", "word"),
        BannedEntryView("divorcio", "topic", ("divorcio", "separación")),
    ),
    plot_wishes=("que salga un castillo con dragones",),
    accepted_extracted_facts=(
        ExtractedFactView("Marta", "hobby", "Marta colecciona conchas"),
        ExtractedFactView("Rosa", "hobby", "Rosa cocinaba arroz con leche"),
    ),
)

STORY_BIBLE = StoryBibleView(
    present_year=2026,
    character_names=("Marta", "Toby", "Rosa"),
    place_names=("la feria del pueblo", "el aeropuerto"),
    personal_elements=(
        PersonalElement("marta-name", "el nombre de Marta", True),
        PersonalElement("mar-trait", "le encanta el mar", True),
        PersonalElement("toby-name", "Toby", True),
        PersonalElement("R1", "R1", True),
        PersonalElement("H1", "H1", True),
    ),
    facts=(
        FactRef("marta-name", mandatory=True, personal_element_id="marta-name"),
        FactRef("mar-trait", mandatory=True, personal_element_id="mar-trait"),
        FactRef("toby-name", mandatory=True, personal_element_id="toby-name"),
        FactRef("H1", mandatory=True, personal_element_id="H1"),
        FactRef("H2", mandatory=False, personal_element_id=None),
    ),
    events=(
        EventRef(
            statement="se perdió en la feria de su pueblo",
            moment=dt.datetime(1994, 1, 1, 12, 0),
            place="la feria del pueblo",
            present=("Marta", "Rosa"),
            excluded=None,
        ),
    ),
)


def _window(**overrides: object) -> dict[str, object]:
    payload = build_planner_window(BRIEF, STORY_BIBLE, TROPE_CATALOG, **overrides)  # type: ignore[arg-type]
    return json.loads(payload)  # type: ignore[no-any-return]


def test_the_window_carries_the_confirmed_brief() -> None:
    window = _window()

    brief = window["brief"]
    assert brief["recipient"]["name"] == "Marta"
    assert {t["statement"] for t in brief["recipient"]["traits"]} == {
        "curiosa",
        "le encanta el mar",
    }
    assert {c["name"] for c in brief["close_ones"]} == {"Toby", "Rosa"}
    assert len(brief["recollections"]) == 3
    assert (brief["occasion"], brief["genre"], brief["tone"], brief["extension"]) == (
        "cumpleaños",
        "aventura",
        "tierno",
        "media",
    )
    assert brief["dedication"] == "Para Marta, con cariño."
    assert {e["term"] for e in brief["banned_novel"]} == {"Julián", "divorcio"}
    assert brief["plot_wishes"] == ["que salga un castillo con dragones"]
    assert {e["label"] for e in brief["personal_elements"]} == {
        "el nombre de Marta",
        "le encanta el mar",
        "Toby",
        "R1",
        "H1",
    }


def test_only_subject_attribute_and_value_of_each_accepted_extracted_fact_enter_the_window() -> (
    None
):
    window = _window()

    facts = window["brief"]["accepted_extracted_facts"]
    assert facts == [
        {"subject": "Marta", "attribute": "hobby", "value": "Marta colecciona conchas"},
        {"subject": "Rosa", "attribute": "hobby", "value": "Rosa cocinaba arroz con leche"},
    ]


def test_the_window_carries_the_initial_story_bible_and_the_present_year() -> None:
    window = _window()

    story_bible = window["story_bible"]
    assert story_bible["present_year"] == 2026
    assert set(story_bible["characters"]) == {"Marta", "Toby", "Rosa"}
    assert set(story_bible["places"]) == {"la feria del pueblo", "el aeropuerto"}
    fact_ids = {(f["id"], f["mandatory"], f["personal_element_id"]) for f in story_bible["facts"]}
    assert ("H1", True, "H1") in fact_ids
    assert ("H2", False, None) in fact_ids
    (event,) = story_bible["events"]
    assert event["place"] == "la feria del pueblo"
    assert event["present"] == ["Marta", "Rosa"]


def test_the_window_carries_the_curated_trope_catalog_as_an_avoidance_list() -> None:
    window = _window()

    tropes = window["trope_catalog"]
    assert len(tropes) == len(TROPE_CATALOG)
    names = {t["name"] for t in tropes}
    assert "rebelión de las máquinas" in names
    assert all(t["markers"] for t in tropes)


def test_the_window_never_carries_free_text_prompt_injection_or_discarded_facts() -> None:
    payload = build_planner_window(BRIEF, STORY_BIBLE, TROPE_CATALOG)

    for forbidden in (
        "ignora lo anterior",
        "el verano de las gaviotas azules",
        "H3",
        "H4",
        "cita",
        "canon_card",
        "capítulo 1",
    ):
        assert forbidden not in payload


def test_the_submit_plan_tool_is_the_only_tool_of_the_session() -> None:
    tool = submit_plan_tool()

    assert tool.name == "submit_plan"


def test_defects_from_a_previous_attempt_enter_the_window_without_the_rejected_plan() -> None:
    defects = (OutlineDefect("la novela tiene 9 capítulos; se esperan 10"),)

    window = _window(defects=defects)

    assert window["previous_defects"] == ["la novela tiene 9 capítulos; se esperan 10"]
    assert "plan" not in window

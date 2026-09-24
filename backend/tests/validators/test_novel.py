"""Validadores deterministas de la etapa 1 y traducción de la etapa 2 de Lean (012-C3, 012-C5,
012-C9, 012-C10, 012-C11)."""

from __future__ import annotations

import datetime as dt

from story_maker.formal.result import ChronologyResult
from story_maker.policy.types import DecisionDePolitica
from story_maker.store.story_bible import (
    BirthEntry,
    CharacterEntry,
    Chronology,
    EventEntry,
    PlaceEntry,
    PresenceEntry,
    StoryBible,
)
from story_maker.validators.novel import (
    BANNED_TERMS_VALIDATOR,
    MANDATORY_ELEMENTS_VALIDATOR,
    BannedTermMatch,
    ChapterText,
    MandatoryElement,
    banned_terms_in_chapters,
    lean_stage_result,
    mandatory_elements_result,
)

ALL_HOLD = dict.fromkeys(("T1", "T2", "T3", "T4", "T5"), True)


# --- 012-C3 · elementos-obligatorios -------------------------------------------------------------


def test_a_mandatory_element_without_use_is_attributed_to_its_outline_chapters() -> None:
    element = MandatoryElement("el_1", "se perdió en la feria", assigned_chapters=(2, 5))

    result = mandatory_elements_result((element,), used_element_ids=frozenset())

    assert result.validator == MANDATORY_ELEMENTS_VALIDATOR
    assert not result.passed
    assert result.score == 0.0
    assert {d.chapter for d in result.defects} == {2, 5}
    assert all(d.blocking and "se perdió en la feria" in d.message for d in result.defects)


def test_an_element_used_in_a_chapter_the_outline_did_not_assign_it_to_still_passes() -> None:
    element = MandatoryElement("el_1", "se perdió en la feria", assigned_chapters=(2, 5))

    result = mandatory_elements_result((element,), used_element_ids=frozenset({"el_1"}))

    assert result.passed
    assert result.defects == ()


def test_an_element_represented_by_several_facts_passes_with_only_one_used() -> None:
    # Modelado de "varios hechos con uno solo usado": el id agregado ya cuenta como usado en
    # cuanto uno de sus hechos tiene un `UsoDeHecho` (quien arma `used_element_ids` decide eso).
    element = MandatoryElement("el_1", "el nombre del destinatario", assigned_chapters=(1,))

    result = mandatory_elements_result((element,), used_element_ids=frozenset({"el_1"}))

    assert result.passed


def test_no_elements_at_all_gives_no_defect() -> None:
    # No mandatory de esta pasada nunca llega a `mandatory_elements_result`: solo se le pasan los
    # obligatorios (`StoryBibleView.mandatory_elements`, 010).
    result = mandatory_elements_result((), used_element_ids=frozenset())

    assert result.passed
    assert result.defects == ()


# --- 012-C5 · palabras-prohibidas aplicado a los capítulos ---------------------------------------


def test_a_banned_term_in_a_chapter_is_attributed_to_that_chapter() -> None:
    chapters = (ChapterText(4, "hubo tormentas aquella noche"),)
    matches = (BannedTermMatch(term="tormenta", level="user", variant="tormentas", chapter=4),)

    result, decision = banned_terms_in_chapters(chapters, matches)

    assert result.validator == BANNED_TERMS_VALIDATOR
    assert not result.passed
    assert result.score == 0.0
    assert len(result.defects) == 1
    defect = result.defects[0]
    assert defect.chapter == 4
    assert defect.blocking
    assert "tormentas" in defect.message
    assert "tormenta" in defect.message
    assert isinstance(decision, DecisionDePolitica)
    assert decision.decision == "deny"
    assert decision.detail == [
        {
            "term": "tormenta",
            "level": "user",
            "variant": "tormentas",
            "location": "chapter",
            "chapter": "4",
        }
    ]


def test_no_matches_leaves_a_single_allow_decision() -> None:
    chapters = (ChapterText(4, "una tarde tranquila"),)

    result, decision = banned_terms_in_chapters(chapters, matches=())

    assert result.passed
    assert result.defects == ()
    assert decision.decision == "allow"
    assert decision.detail is None


def test_every_match_lands_in_the_single_decision_of_the_pass() -> None:
    chapters = (ChapterText(2, "..."), ChapterText(4, "..."))
    matches = (
        BannedTermMatch("tormenta", "user", "tormentas", 4),
        BannedTermMatch("dron", "global", "drones", 2),
    )

    result, decision = banned_terms_in_chapters(chapters, matches)

    assert len(result.defects) == 2
    assert {d.chapter for d in result.defects} == {2, 4}
    assert decision.decision == "deny"
    assert decision.detail is not None
    assert len(decision.detail) == 2


# --- 012-C9, 012-C10, 012-C11 · traducción del resultado de Lean ---------------------------------


def _entry(
    id_: int,
    moment: dt.datetime,
    place: int,
    *present: int,
    origin: str = "recorded",
    chapter: int | None = None,
    beat: int | None = None,
    excluded: int | None = None,
) -> EventEntry:
    return EventEntry(
        id=id_,
        statement=f"enunciado {id_}",
        moment=moment,
        place_id=place,
        presences=tuple(PresenceEntry(p, None) for p in present),
        type="exclusion" if excluded is not None else "ordinary",
        excluded_character_id=excluded,
        analepsis=False,
        origin=origin,
        chapter=chapter,
        beat=beat,
    )


def _bible(*events: EventEntry) -> StoryBible:
    characters = (
        CharacterEntry(11, "recipient", "person", "Marta", dt.date(1990, 5, 14), "brief"),
        CharacterEntry(12, "close_one", "person", "Rosa", dt.date(1936, 2, 29), "brief"),
    )
    places = (
        PlaceEntry(21, "la feria del pueblo", "", "brief"),
        PlaceEntry(22, "la estación", "", "brief"),
    )
    return StoryBible(
        version_id=1,
        present_year=2026,
        world=None,
        characters=characters,
        places=places,
        facts=(),
        chronology=Chronology(
            events=events,
            births=(BirthEntry(11, dt.date(1990, 5, 14)), BirthEntry(12, dt.date(1936, 2, 29))),
            novum_date=dt.date(2024, 11, 1),
        ),
    )


def test_a_violated_invariant_with_a_narrated_witness_is_attributable() -> None:
    bible = _bible(
        _entry(32, dt.datetime(2010, 9, 1, 12, 0), 22, origin="brief", excluded=12),
        _entry(71, dt.datetime(2026, 8, 15, 12, 0), 21, 12, chapter=6, beat=2),
    )
    result = ChronologyResult(
        "failed", holds={**ALL_HOLD, "T4": False}, witnesses={"T4": (12, 32, 71)}
    )

    stage = lean_stage_result(result, bible)

    assert not stage.passed
    assert stage.score == 0.0
    assert not stage.unattributable
    assert stage.internal_error is None
    assert [d.chapter for d in stage.defects] == [6]
    assert all(d.blocking for d in stage.defects)


def test_a_witness_with_only_brief_events_is_unattributable() -> None:
    bible = _bible(
        _entry(31, dt.datetime(1998, 5, 14, 12, 0), 21, 11, 12, origin="brief"),
        _entry(33, dt.datetime(1998, 5, 14, 12, 0), 22, 11, origin="brief"),
    )
    result = ChronologyResult(
        "failed", holds={**ALL_HOLD, "T3": False}, witnesses={"T3": (11, 31, 33)}
    )

    stage = lean_stage_result(result, bible)

    assert not stage.passed
    assert stage.unattributable
    assert stage.internal_error is None
    assert [d.chapter for d in stage.defects] == [None]


def test_a_non_compiling_file_gives_the_internal_error_reason_and_no_defects() -> None:
    bible = _bible()
    result = ChronologyResult("error", reason="no compila: sintaxis")

    stage = lean_stage_result(result, bible)

    assert not stage.passed
    assert stage.score == 0.0
    assert not stage.unattributable
    assert stage.internal_error == "no compila: sintaxis"
    assert stage.defects == ()

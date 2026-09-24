"""`outline`: juicio de un plan contra la story bible inicial (010-C10..C16, 010-I6).

Los datos de prueba son los del brief de referencia de `specs/backend/010-planificacion.md`:
Marta (destinataria), Toby y Rosa (allegados), R1/R2/R3 (recuerdos), H1/H2 (hechos aceptados),
novela creada 2026-03-10 → año presente 2026. El plan de referencia tiene 10 capítulos de 3
beats, todos los obligatorios asignados al capítulo 1, un novum del 2021-05-01 con 3
consecuencias, e inventa a Nia (capítulo 4) y «el puerto nuevo» (capítulo 7)."""

from __future__ import annotations

import datetime as dt

import pytest

from story_maker.pipeline.planning.plan import (
    Beat,
    InventedCharacter,
    InventedFact,
    InventedPlace,
    OutlineChapterSubmission,
    PlannedEvent,
    PlanSubmission,
    StyleSheetSubmission,
    TreatmentException,
    WorldSubmission,
)
from story_maker.pipeline.planning.story_bible_view import PersonalElement, StoryBibleView
from story_maker.validators.outline import judge_outline

PRESENT_YEAR = 2026

STORY_BIBLE = StoryBibleView(
    present_year=PRESENT_YEAR,
    character_names=("Marta", "Toby", "Rosa"),
    place_names=("la feria del pueblo", "el aeropuerto"),
    fact_ids=(
        "marta-name",
        "mar-trait",
        "toby-name",
        "toby-relationship",
        "rosa-name",
        "rosa-relationship",
        "R1",
        "R2",
        "R3",
        "H1",
        "H2",
    ),
    personal_elements=(
        PersonalElement(id="marta-name", label="el nombre de Marta", mandatory=True),
        PersonalElement(id="mar-trait", label="le encanta el mar", mandatory=True),
        PersonalElement(id="toby-name", label="Toby", mandatory=True),
        PersonalElement(id="R1", label="R1", mandatory=True),
        PersonalElement(id="H1", label="H1", mandatory=True),
        PersonalElement(id="rosa-name", label="Rosa", mandatory=False),
        PersonalElement(id="R2", label="R2", mandatory=False),
        PersonalElement(id="R3", label="R3", mandatory=False),
        PersonalElement(id="H2", label="H2", mandatory=False),
    ),
)

MANDATORY_IDS = ("marta-name", "mar-trait", "toby-name", "R1", "H1")


def _beats(count: int = 3) -> tuple[Beat, ...]:
    return tuple(Beat(number=n, description=f"Beat {n}.") for n in range(1, count + 1))


def _chapter(
    number: int, *, beats: tuple[Beat, ...] | None = None, assigned: tuple[str, ...] = ()
) -> OutlineChapterSubmission:
    return OutlineChapterSubmission(
        number=number,
        title=f"Capítulo {number}",
        arc_function="función en el arco",
        beats=beats if beats is not None else _beats(),
        assigned_elements=assigned,
    )


def reference_plan() -> PlanSubmission:
    chapters = [_chapter(n) for n in range(1, 11)]
    chapters[0] = _chapter(1, assigned=MANDATORY_IDS)
    chapters[3] = _chapter(
        4,
        beats=(
            Beat(
                number=1,
                description="Marta conoce a Nia.",
                characters=("Nia",),
                events=(
                    PlannedEvent(
                        statement="Marta conoce a Nia.",
                        moment=dt.datetime(2026, 3, 1, 10, 0),
                        place="la feria del pueblo",
                        type="ordinary",
                        analepsis=False,
                        present=("Marta", "Nia"),
                    ),
                ),
            ),
            *_beats()[1:],
        ),
    )
    chapters[6] = _chapter(
        7,
        beats=(
            Beat(
                number=1,
                description="Rosa visita el puerto nuevo.",
                events=(
                    PlannedEvent(
                        statement="Rosa visita el puerto nuevo.",
                        moment=dt.datetime(2026, 4, 1, 10, 0),
                        place="el puerto nuevo",
                        type="ordinary",
                        analepsis=False,
                        present=("Rosa",),
                    ),
                ),
            ),
            *_beats()[1:],
        ),
    )
    return PlanSubmission(
        world=WorldSubmission(
            novum_description="Las IA razonan sobre sus propios límites éticos.",
            novum_scope="technological",
            novum_date=dt.date(2021, 5, 1),
            consequences=["Una.", "Dos.", "Tres."],
        ),
        characters=(InventedCharacter(name="Nia", species="artificial"),),
        places=(InventedPlace(name="el puerto nuevo"),),
        facts=(InventedFact(id="nia-origin", subject="Nia", attribute="origin", value="2021."),),
        chapters=tuple(chapters),
        style_sheet=StyleSheetSubmission(
            narrator="third",
            tense="past",
            default_treatment="tu",
            treatment_exceptions=(TreatmentException(a="Marta", b="Rosa", treatment="tu"),),
        ),
        title="El verano de Marta",
    )


def _with_chapters(
    plan: PlanSubmission, chapters: tuple[OutlineChapterSubmission, ...]
) -> PlanSubmission:
    return plan.model_copy(update={"chapters": chapters})


def _replace_chapter(plan: PlanSubmission, chapter: OutlineChapterSubmission) -> PlanSubmission:
    chapters = tuple(chapter if c.number == chapter.number else c for c in plan.chapters)
    return _with_chapters(plan, chapters)


def _with_first_beat(plan: PlanSubmission, chapter_number: int, beat: Beat) -> PlanSubmission:
    chapter = next(c for c in plan.chapters if c.number == chapter_number)
    beats = (beat, *chapter.beats[1:])
    return _replace_chapter(plan, chapter.model_copy(update={"beats": beats}))


def _with_event(plan: PlanSubmission, chapter_number: int, event: PlannedEvent) -> PlanSubmission:
    chapter = next(c for c in plan.chapters if c.number == chapter_number)
    return _with_first_beat(
        plan, chapter_number, chapter.beats[0].model_copy(update={"events": (event,)})
    )


def _messages(result: object) -> tuple[str, ...]:
    return tuple(d.message for d in result.defects)  # type: ignore[attr-defined]


def test_the_reference_plan_passes_without_defects() -> None:
    """010-C10: ningún validador exige que se cumpla un deseo de trama."""
    result = judge_outline(reference_plan(), STORY_BIBLE, present_year=PRESENT_YEAR)

    assert result.passed
    assert result.defects == ()
    assert result.score == 1.0


@pytest.mark.parametrize(
    ("chapter_count", "expect_defect"),
    [(9, True), (11, True), (10, False)],
)
def test_the_number_of_chapters(chapter_count: int, expect_defect: bool) -> None:
    plan = reference_plan()
    if chapter_count == 9:
        plan = _with_chapters(plan, plan.chapters[:9])
    elif chapter_count == 11:
        plan = _with_chapters(plan, (*plan.chapters, _chapter(11)))

    result = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    has_count_defect = any("novela tiene" in m for m in _messages(result))
    assert has_count_defect is expect_defect


@pytest.mark.parametrize(
    ("chapter_5_beats", "chapter_6_beats", "expect_defect_on_5"),
    [(2, 3, True), (7, 3, True), (3, 6, False)],
)
def test_beats_per_chapter(
    chapter_5_beats: int, chapter_6_beats: int, expect_defect_on_5: bool
) -> None:
    plan = reference_plan()
    plan = _replace_chapter(plan, _chapter(5, beats=_beats(chapter_5_beats)))
    plan = _replace_chapter(plan, _chapter(6, beats=_beats(chapter_6_beats)))

    result = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    beat_defects = [d for d in result.defects if "beats" in d.message]
    assert bool(beat_defects) is expect_defect_on_5
    if beat_defects:
        assert all(d.chapter == 5 for d in beat_defects)


def test_a_mandatory_element_without_any_chapter_assigned_is_named() -> None:
    plan = reference_plan()
    plan = _replace_chapter(plan, _chapter(1, assigned=("mar-trait", "toby-name", "R1", "H1")))

    result = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    assert any("el nombre de Marta" in m for m in _messages(result))


def test_r1_without_any_chapter_assigned_is_named() -> None:
    plan = reference_plan()
    plan = _replace_chapter(
        plan, _chapter(1, assigned=("marta-name", "mar-trait", "toby-name", "H1"))
    )

    result = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    assert any(m == "«R1» no está asignado a ningún capítulo" for m in _messages(result))


def test_h1_assigned_only_to_a_chapter_outside_1_to_10() -> None:
    plan = reference_plan()
    plan = _replace_chapter(
        plan, _chapter(1, assigned=("marta-name", "mar-trait", "toby-name", "R1"))
    )
    plan = _with_chapters(plan, (*plan.chapters, _chapter(11, assigned=("H1",))))

    result = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    (defect,) = [d for d in result.defects if "H1" in d.message]
    assert "fuera de 1-10" in defect.message
    assert "queda sin asignar" in defect.message


def test_an_assignment_to_an_element_that_does_not_exist_in_the_brief_is_a_reference_defect() -> (
    None
):
    plan = reference_plan()
    plan = _replace_chapter(plan, _chapter(1, assigned=(*MANDATORY_IDS, "elemento-fantasma")))

    result = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    (defect,) = [d for d in result.defects if "elemento-fantasma" in d.message]
    assert defect.chapter == 1
    assert "no existe en el brief" in defect.message


def test_every_mandatory_element_assigned_to_1_through_10_has_no_assignment_defect() -> None:
    result = judge_outline(reference_plan(), STORY_BIBLE, present_year=PRESENT_YEAR)

    assert not any("asignad" in m or "no existe en el brief" in m for m in _messages(result))


@pytest.mark.parametrize(
    ("analepsis", "moment", "expect_defect"),
    [
        (False, dt.datetime(2026, 1, 1, 0, 0), False),
        (False, dt.datetime(2026, 12, 31, 23, 59), False),
        (False, dt.datetime(2025, 12, 31, 23, 59), True),
        (True, dt.datetime(2025, 12, 31, 23, 59), False),
        (True, dt.datetime(2026, 2, 1, 0, 0), False),
        (False, dt.datetime(2027, 1, 1, 0, 0), True),
        (True, dt.datetime(2027, 1, 1, 0, 0), True),
    ],
)
def test_event_moments_against_the_present_year(
    analepsis: bool, moment: dt.datetime, expect_defect: bool
) -> None:
    event = PlannedEvent(
        statement="Un evento.",
        moment=moment,
        place="la feria del pueblo",
        type="ordinary",
        analepsis=analepsis,
        present=("Marta",),
    )
    plan = _with_event(reference_plan(), 1, event)

    result = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    has_defect = any("año presente" in m for m in _messages(result))
    assert has_defect is expect_defect
    if has_defect:
        (defect,) = [d for d in result.defects if "año presente" in d.message]
        assert defect.chapter == 1


def test_an_event_with_a_present_that_does_not_exist_is_attributed_to_its_chapter() -> None:
    event = PlannedEvent(
        statement="Un evento.",
        moment=dt.datetime(2026, 6, 1),
        place="la feria del pueblo",
        type="ordinary",
        analepsis=False,
        present=("Fantasma",),
    )
    plan = _with_event(reference_plan(), 1, event)

    result = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    (defect,) = [d for d in result.defects if "Fantasma" in d.message]
    assert defect.chapter == 1


def test_an_event_with_a_place_that_does_not_exist_is_attributed_to_its_chapter() -> None:
    event = PlannedEvent(
        statement="Un evento.",
        moment=dt.datetime(2026, 6, 1),
        place="lugar fantasma",
        type="ordinary",
        analepsis=False,
        present=("Marta",),
    )
    plan = _with_event(reference_plan(), 1, event)

    result = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    (defect,) = [d for d in result.defects if "lugar fantasma" in d.message]
    assert defect.chapter == 1


def test_an_exclusion_event_with_an_excluded_that_does_not_exist_is_a_defect() -> None:
    event = PlannedEvent(
        statement="Un evento.",
        moment=dt.datetime(2026, 6, 1),
        place="la feria del pueblo",
        type="exclusion",
        excluded="Fantasma",
        analepsis=False,
        present=("Marta",),
    )
    plan = _with_event(reference_plan(), 1, event)

    result = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    assert any("excluyente" in m for m in _messages(result))


def test_an_exclusion_event_without_an_excluded_is_a_defect() -> None:
    event = PlannedEvent(
        statement="Un evento.",
        moment=dt.datetime(2026, 6, 1),
        place="la feria del pueblo",
        type="exclusion",
        excluded=None,
        analepsis=False,
        present=("Marta",),
    )
    plan = _with_event(reference_plan(), 1, event)

    result = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    assert any("excluyente" in m for m in _messages(result))


def test_an_ordinary_event_with_an_excluded_is_a_defect() -> None:
    event = PlannedEvent(
        statement="Un evento.",
        moment=dt.datetime(2026, 6, 1),
        place="la feria del pueblo",
        type="ordinary",
        excluded="Rosa",
        analepsis=False,
        present=("Marta",),
    )
    plan = _with_event(reference_plan(), 1, event)

    result = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    assert any("ordinario" in m for m in _messages(result))


def test_a_beat_that_uses_a_character_that_does_not_exist_is_attributed_to_its_chapter() -> None:
    plan = reference_plan()
    plan = _with_first_beat(plan, 1, Beat(number=1, description="Beat.", characters=("Fantasma",)))

    result = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    (defect,) = [d for d in result.defects if "Fantasma" in d.message]
    assert defect.chapter == 1


def test_a_beat_that_uses_a_fact_that_does_not_exist_is_attributed_to_its_chapter() -> None:
    plan = reference_plan()
    plan = _with_first_beat(
        plan, 1, Beat(number=1, description="Beat.", facts_used=("hecho-fantasma",))
    )

    result = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    (defect,) = [d for d in result.defects if "hecho-fantasma" in d.message]
    assert defect.chapter == 1


def test_an_invented_fact_whose_subject_does_not_exist_is_a_defect() -> None:
    plan = reference_plan()
    plan = plan.model_copy(
        update={
            "facts": (
                *plan.facts,
                InventedFact(id="f-2", subject="Fantasma", attribute="origin", value="x"),
            )
        }
    )

    result = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    assert any("Fantasma" in m for m in _messages(result))


def test_a_treatment_exception_with_a_character_that_does_not_exist_is_a_defect() -> None:
    plan = reference_plan()
    plan = plan.model_copy(
        update={
            "style_sheet": plan.style_sheet.model_copy(
                update={
                    "treatment_exceptions": (
                        TreatmentException(a="Fantasma", b="Marta", treatment="tu"),
                    )
                }
            )
        }
    )

    result = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    assert any("Fantasma" in m for m in _messages(result))


def test_events_with_marta_rosa_nia_the_fair_and_the_new_port_are_valid() -> None:
    """010-C14, última fila: personajes y lugares del brief y los que el plan inventa."""
    result = judge_outline(reference_plan(), STORY_BIBLE, present_year=PRESENT_YEAR)

    assert not any("no existe" in m for m in _messages(result))


@pytest.mark.parametrize(
    ("novum_date", "expect_defect"),
    [(dt.date(2025, 12, 31), False), (dt.date(2026, 1, 1), True)],
)
def test_the_novum_date_must_be_before_the_present_year(
    novum_date: dt.date, expect_defect: bool
) -> None:
    plan = reference_plan()
    world = plan.world.model_copy(update={"novum_date": novum_date})
    plan = plan.model_copy(update={"world": world})

    result = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    assert any("novum" in m for m in _messages(result)) is expect_defect


def test_outline_does_not_judge_chronology() -> None:
    """010-C16: T1-T5 los comprueba Lean sobre la cronología registrada, nunca `outline`."""
    plan = reference_plan()
    # Rosa presente en un evento del capítulo 5 (posterior a su partida definitiva, R2 en el
    # brief) y un evento del capítulo 3 anterior a uno del capítulo 2: `outline` no lo mira.
    plan = _with_event(
        plan,
        5,
        PlannedEvent(
            statement="Rosa vuelve a aparecer.",
            moment=dt.datetime(2026, 8, 1),
            place="la feria del pueblo",
            type="ordinary",
            analepsis=False,
            present=("Rosa",),
        ),
    )
    plan = _with_event(
        plan,
        2,
        PlannedEvent(
            statement="Evento tardío.",
            moment=dt.datetime(2026, 6, 1),
            place="la feria del pueblo",
            type="ordinary",
            analepsis=False,
            present=("Marta",),
        ),
    )
    plan = _with_event(
        plan,
        3,
        PlannedEvent(
            statement="Evento temprano.",
            moment=dt.datetime(2026, 1, 5),
            place="la feria del pueblo",
            type="ordinary",
            analepsis=False,
            present=("Marta",),
        ),
    )

    result = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    assert result.passed
    assert result.defects == ()


def test_outline_is_deterministic() -> None:
    """010-I6: el mismo plan y la misma story bible dan siempre los mismos defectos."""
    plan = reference_plan()
    plan = _with_chapters(plan, plan.chapters[:9])

    first = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)
    second = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    assert first.defects == second.defects


def test_outline_is_exhaustive_in_a_single_judgement() -> None:
    """010-I6: un plan con defectos de capítulos, de momento y de referencia da los tres."""
    plan = reference_plan()
    plan = _with_chapters(plan, plan.chapters[:9])
    plan = _with_event(
        plan,
        1,
        PlannedEvent(
            statement="Fuera de año.",
            moment=dt.datetime(2027, 1, 1),
            place="la feria del pueblo",
            type="ordinary",
            analepsis=False,
            present=("Marta",),
        ),
    )
    plan = _with_first_beat(plan, 2, Beat(number=1, description="Beat.", characters=("Fantasma",)))

    result = judge_outline(plan, STORY_BIBLE, present_year=PRESENT_YEAR)

    messages = _messages(result)
    assert any("novela tiene" in m for m in messages)
    assert any("año presente" in m for m in messages)
    assert any("Fantasma" in m for m in messages)

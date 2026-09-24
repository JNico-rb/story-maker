"""`outline`: valida un plan contra la story bible inicial, determinista y exhaustivo, sin
comprobar la cronología (010-C10..C16, 010-I6; `architecture.md` §5.2, §11.2, §11.4).

No juzga T1-T5 (los comprueba Lean sobre la cronología registrada, nunca sobre la planificada:
`domain-knowledge.md` §5.3, `verification.md` §5 fila 4.1)."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from story_maker.domain.constants import CHAPTERS_PER_NOVEL, MAX_BEATS, MIN_BEATS
from story_maker.pipeline.planning.plan import (
    WORLD_SUBJECT,
    Beat,
    OutlineChapterSubmission,
    PlannedEvent,
    PlanSubmission,
)
from story_maker.pipeline.planning.story_bible_view import StoryBibleView


@dataclass(frozen=True)
class OutlineDefect:
    message: str
    chapter: int | None = None


@dataclass(frozen=True)
class OutlineResult:
    passed: bool
    defects: tuple[OutlineDefect, ...]

    @property
    def score(self) -> float:
        return 1.0 if self.passed else 0.0


def judge_outline(
    plan: PlanSubmission, story_bible: StoryBibleView, *, present_year: int
) -> OutlineResult:
    """Un solo juicio, siempre con los mismos defectos para el mismo plan y la misma story
    bible (010-I6): nunca se corta en el primer defecto que encuentra."""
    names = _known_names(plan, story_bible)
    defects = (
        *_chapter_count_defects(plan),
        *_beat_count_defects(plan),
        *_mandatory_element_defects(plan, story_bible),
        *_assigned_element_reference_defects(plan, story_bible),
        *_moment_defects(plan, present_year),
        *_novum_defects(plan, present_year),
        *_event_reference_defects(plan, names),
        *_beat_reference_defects(plan, names, story_bible),
        *_fact_subject_defects(plan, names),
        *_treatment_exception_defects(plan, names),
    )
    return OutlineResult(passed=not defects, defects=defects)


@dataclass(frozen=True)
class _KnownNames:
    characters: frozenset[str]
    places: frozenset[str]


def _known_names(plan: PlanSubmission, story_bible: StoryBibleView) -> _KnownNames:
    """Una referencia es válida si apunta a la story bible inicial o a lo que el mismo plan
    inventa (010-C14)."""
    return _KnownNames(
        characters=frozenset(story_bible.character_names) | {c.name for c in plan.characters},
        places=frozenset(story_bible.place_names) | {p.name for p in plan.places},
    )


def _chapter_count_defects(plan: PlanSubmission) -> tuple[OutlineDefect, ...]:
    if len(plan.chapters) == CHAPTERS_PER_NOVEL:
        return ()
    return (OutlineDefect(f"la novela tiene {len(plan.chapters)} capítulos; se esperan 10"),)


def _beat_count_defects(plan: PlanSubmission) -> tuple[OutlineDefect, ...]:
    return tuple(
        OutlineDefect(f"el capítulo {c.number} tiene {len(c.beats)} beats; van de 3 a 6", c.number)
        for c in plan.chapters
        if not MIN_BEATS <= len(c.beats) <= MAX_BEATS
    )


def _mandatory_element_defects(
    plan: PlanSubmission, story_bible: StoryBibleView
) -> tuple[OutlineDefect, ...]:
    defects: list[OutlineDefect] = []
    for element in story_bible.mandatory_elements:
        in_range, out_of_range = _assignments(plan, element.id)
        if in_range:
            continue
        if out_of_range:
            chapters = ", ".join(str(n) for n in out_of_range)
            defects.append(
                OutlineDefect(
                    f"«{element.label}» solo está asignado a capítulos fuera de 1-10 ({chapters}); "
                    "queda sin asignar"
                )
            )
        else:
            defects.append(OutlineDefect(f"«{element.label}» no está asignado a ningún capítulo"))
    return tuple(defects)


def _assignments(plan: PlanSubmission, element_id: str) -> tuple[list[int], list[int]]:
    in_range = [
        c.number
        for c in plan.chapters
        if element_id in c.assigned_elements and 1 <= c.number <= CHAPTERS_PER_NOVEL
    ]
    out_of_range = [
        c.number
        for c in plan.chapters
        if element_id in c.assigned_elements and not (1 <= c.number <= CHAPTERS_PER_NOVEL)
    ]
    return in_range, out_of_range


def _assigned_element_reference_defects(
    plan: PlanSubmission, story_bible: StoryBibleView
) -> tuple[OutlineDefect, ...]:
    known = {e.id for e in story_bible.personal_elements}
    return tuple(
        OutlineDefect(f"asigna al elemento «{eid}», que no existe en el brief", c.number)
        for c in plan.chapters
        for eid in c.assigned_elements
        if eid not in known
    )


def _moment_defects(plan: PlanSubmission, present_year: int) -> tuple[OutlineDefect, ...]:
    defects: list[OutlineDefect] = []
    for chapter, _beat, event in _events(plan):
        year = event.moment.year
        if year > present_year:
            defects.append(
                OutlineDefect(
                    f"el evento «{event.statement}» es posterior al año presente", chapter.number
                )
            )
        elif year < present_year and not event.analepsis:
            defects.append(
                OutlineDefect(
                    f"el evento «{event.statement}» queda fuera del año presente sin analepsis",
                    chapter.number,
                )
            )
    return tuple(defects)


def _novum_defects(plan: PlanSubmission, present_year: int) -> tuple[OutlineDefect, ...]:
    if plan.world.novum_date < dt.date(present_year, 1, 1):
        return ()
    return (OutlineDefect("el novum no es anterior al año presente"),)


def _event_reference_defects(plan: PlanSubmission, names: _KnownNames) -> tuple[OutlineDefect, ...]:
    defects: list[OutlineDefect] = []
    for chapter, _beat, event in _events(plan):
        for present in event.present:
            if present not in names.characters:
                defects.append(OutlineDefect(f"el presente «{present}» no existe", chapter.number))
        if event.place not in names.places:
            defects.append(OutlineDefect(f"el lugar «{event.place}» no existe", chapter.number))
        defects.extend(_exclusion_defects(chapter, event, names))
    return tuple(defects)


def _exclusion_defects(
    chapter: OutlineChapterSubmission, event: PlannedEvent, names: _KnownNames
) -> tuple[OutlineDefect, ...]:
    if event.type == "exclusion":
        if event.excluded is None or event.excluded not in names.characters:
            return (OutlineDefect("evento excluyente sin un excluido válido", chapter.number),)
        return ()
    if event.excluded is not None:
        return (OutlineDefect("evento ordinario con un excluido", chapter.number),)
    return ()


def _beat_reference_defects(
    plan: PlanSubmission, names: _KnownNames, story_bible: StoryBibleView
) -> tuple[OutlineDefect, ...]:
    fact_ids = set(story_bible.fact_ids) | {f.id for f in plan.facts}
    defects: list[OutlineDefect] = []
    for chapter, beat in _beats(plan):
        for name in beat.characters:
            if name not in names.characters:
                message = f"el beat usa el personaje «{name}», que no existe"
                defects.append(OutlineDefect(message, chapter.number))
        for fact_id in beat.facts_used:
            if fact_id not in fact_ids:
                message = f"el beat usa el hecho «{fact_id}», que no existe"
                defects.append(OutlineDefect(message, chapter.number))
    return tuple(defects)


def _fact_subject_defects(plan: PlanSubmission, names: _KnownNames) -> tuple[OutlineDefect, ...]:
    valid = names.characters | names.places | {WORLD_SUBJECT}
    return tuple(
        OutlineDefect(f"el hecho «{fact.id}» tiene un sujeto que no existe: «{fact.subject}»")
        for fact in plan.facts
        if fact.subject not in valid
    )


def _treatment_exception_defects(
    plan: PlanSubmission, names: _KnownNames
) -> tuple[OutlineDefect, ...]:
    defects: list[OutlineDefect] = []
    for exception in plan.style_sheet.treatment_exceptions:
        for name in (exception.a, exception.b):
            if name not in names.characters:
                defects.append(
                    OutlineDefect(
                        f"la excepción de tratamiento usa el personaje «{name}», que no existe"
                    )
                )
    return tuple(defects)


def _beats(plan: PlanSubmission) -> list[tuple[OutlineChapterSubmission, Beat]]:
    return [(chapter, beat) for chapter in plan.chapters for beat in chapter.beats]


def _events(
    plan: PlanSubmission,
) -> list[tuple[OutlineChapterSubmission, Beat, PlannedEvent]]:
    return [(chapter, beat, event) for chapter, beat in _beats(plan) for event in beat.events]

"""La validación de una propuesta por el código, sobre la story bible de la versión base
(`architecture.md` §10.1 paso 3; 014-C06). Cada defecto es un texto que recibe el planner en su
sesión siguiente."""

from __future__ import annotations

from collections.abc import Callable

from story_maker.domain.constants import NAME, RECOLLECTION, RELATIONSHIP, TRAIT
from story_maker.pipeline.changes.proposal import NewFact, ProposeChangeInput
from story_maker.pipeline.changes.selection import FactSelection, FragmentSelection
from story_maker.policy.types import DecisionDePolitica
from story_maker.store.story_bible import FactEntry, StoryBible

BRIEF_ATTRIBUTES = frozenset({NAME, TRAIT, RELATIONSHIP, RECOLLECTION})
# Los hechos que el cliente dio (brief o texto libre) solo cambian si están en la selección.
CLIENT_ORIGINS = frozenset({"brief", "free_text"})

Judge = Callable[[str], DecisionDePolitica]


def proposal_defects(
    proposal: ProposeChangeInput,
    bible: StoryBible,
    selection: FactSelection | FragmentSelection,
    judge: Judge,
) -> list[str]:
    """`judge` pasa un valor nuevo por el motor de políticas (y deja su decisión)."""
    facts = {fact.id: fact for fact in bible.facts}
    defects: list[str] = []
    for change in proposal.changes:
        fact = facts.get(change.fact_id)
        if fact is None:
            defects.append(f"Hecho inexistente en la versión vigente: {change.fact_id}")
            continue
        if not change.new_value.strip() or change.new_value == fact.value:
            defects.append(f"El cambio no cambia nada: hecho {fact.id}")
            continue
        if fact.origin in CLIENT_ORIGINS and not _in_selection(fact, bible, selection):
            defects.append(f"Hecho del brief fuera de la selección: {fact.id}")
        defects.extend(_banned(judge, change.new_value))
    if proposal.new_fact is not None:
        defects.extend(_new_fact_defects(proposal.new_fact, bible, judge))
    return defects


def _new_fact_defects(new_fact: NewFact, bible: StoryBible, judge: Judge) -> list[str]:
    subjects = bible.characters if new_fact.subject_type == "character" else bible.places
    defects: list[str] = []
    if new_fact.subject_id not in {subject.id for subject in subjects}:
        defects.append(f"Sujeto inexistente: {new_fact.subject_type} {new_fact.subject_id}")
    if new_fact.attribute not in BRIEF_ATTRIBUTES:
        defects.append(f"Atributo fuera del vocabulario: {new_fact.attribute}")
    return defects + _banned(judge, new_fact.value)


def _banned(judge: Judge, value: str) -> list[str]:
    decision = judge(value)
    if decision.decision != "deny":
        return []
    item = (decision.detail or [{}])[0]
    return [f"Prohibida en el valor nuevo: término={item.get('term')}, nivel={item.get('level')}"]


def _in_selection(
    fact: FactEntry, bible: StoryBible, selection: FactSelection | FragmentSelection
) -> bool:
    """El hecho seleccionado o, con un fragmento, uno cuyo sujeto aparece en su capítulo."""
    if isinstance(selection, FactSelection):
        return fact.id == selection.fact_id
    return _appears(fact, bible, selection.chapter)


def _appears(fact: FactEntry, bible: StoryBible, chapter: int) -> bool:
    """La relación «aparece» de la `FichaDePersonajes` (`definitions.md` §3): un `UsoDeHecho`
    de alguno de sus hechos en el capítulo, o un evento registrado en él con el personaje
    presente o que ocurre en el lugar."""
    same_subject = [
        other
        for other in bible.facts
        if (other.character_id, other.place_id) == (fact.character_id, fact.place_id)
    ]
    if any(chapter in other.chapters for other in same_subject):
        return True
    for event in bible.chronology.events:
        if event.origin != "recorded" or event.chapter != chapter:
            continue
        if fact.place_id is not None and event.place_id == fact.place_id:
            return True
        present = (p.character_id for p in event.presences)
        if fact.character_id is not None and fact.character_id in present:
            return True
    return False

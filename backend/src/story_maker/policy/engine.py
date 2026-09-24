"""MotorDePoliticas: función pura que decide allow | deny | flag (architecture.md §12.2)."""

from story_maker.domain.banned_terms import find_term_matches
from story_maker.policy.types import DecisionDePolitica, EntradaProhibida, PeticionDePolitica
from story_maker.policy.whitelist import ALLOWED_SKILL, is_tool_allowed


def _applies(entry: EntradaProhibida, peticion: PeticionDePolitica) -> bool:
    if entry.level == "global":
        return True
    if entry.level == "user":
        return entry.owner == peticion.cliente
    return entry.owner == peticion.novela


def _check_banned_terms(peticion: PeticionDePolitica) -> DecisionDePolitica | None:
    for entry in peticion.banned_entries:
        if not _applies(entry, peticion):
            continue
        needles = entry.keywords if entry.type == "topic" else [entry.term]
        for campo in peticion.campos:
            if not campo.narrativo:
                continue
            for needle in needles:
                for variant in find_term_matches(campo.texto, needle):
                    return DecisionDePolitica(
                        decision="deny",
                        rule="palabras-prohibidas",
                        detail=[{"term": entry.term, "level": entry.level, "variant": variant}],
                    )
    return None


def _check_whitelist(peticion: PeticionDePolitica) -> DecisionDePolitica | None:
    if peticion.rol is None or peticion.tool is None:
        return None
    if not is_tool_allowed(peticion.rol, peticion.tool):
        return DecisionDePolitica(
            decision="deny",
            rule="lista-blanca",
            detail=[{"role": peticion.rol, "tool": peticion.tool}],
        )
    if peticion.tool == "Skill" and peticion.skill is not None and peticion.skill != ALLOWED_SKILL:
        return DecisionDePolitica(
            decision="deny",
            rule="skill-no-admitida",
            detail=[{"skill": peticion.skill}],
        )
    return None


def decide(peticion: PeticionDePolitica) -> DecisionDePolitica:
    decision = _check_whitelist(peticion)
    if decision is not None:
        return decision
    decision = _check_banned_terms(peticion)
    if decision is not None:
        return decision
    return DecisionDePolitica(decision="allow")

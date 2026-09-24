"""MotorDePoliticas: función pura que decide allow | deny | flag (architecture.md §12.2)."""

from story_maker.domain.banned_terms import find_term_matches
from story_maker.policy.types import DecisionDePolitica, EntradaProhibida, PeticionDePolitica


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


def decide(peticion: PeticionDePolitica) -> DecisionDePolitica:
    decision = _check_banned_terms(peticion)
    if decision is not None:
        return decision
    return DecisionDePolitica(decision="allow")

"""El lint en vivo: lo que el texto de un capítulo choca con la versión vigente, sin registrar
nada (`architecture.md` §10.3; 019-C01 a 019-C08, 019-I2)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from story_maker.config import Config
from story_maker.domain.banned_terms import find_term_matches, normalize_token, tokenize
from story_maker.domain.constants import NOMINAL_ATTRIBUTES
from story_maker.lint.chapter import LintInputs, lint_chapter
from story_maker.pipeline.manual_edit.checks import (
    active_banned,
    banned_diagnostics,
    name_variant_diagnostics,
)
from story_maker.pipeline.manual_edit.chronology import (
    load_births,
    load_timeline,
    reappearances,
    wrong_ages,
)
from story_maker.pipeline.manual_edit.diagnostics import Diagnostic, ordered
from story_maker.pipeline.prose_lint import lint_inputs, threshold_comment
from story_maker.store.models import Chapter, Character, Fact, FactUsage, Novel, Place
from story_maker.validators.exact_names import letter_words, name_variants

_LETTERS = re.compile(r"[^\W\d_]+")


@dataclass(frozen=True)
class UsedFact:
    """Un hecho nominal con `UsoDeHecho` en el capítulo editado."""

    subject: str
    attribute: str
    value: str


@dataclass(frozen=True)
class Vigente:
    """Lo que el lint lee de la versión vigente, una vez por petición."""

    canonical_names: tuple[str, ...]
    known_words: frozenset[str]  # en forma normalizada, de todos sus capítulos
    used_facts: tuple[UsedFact, ...]


def _subject(session: Session, fact: Fact) -> str:
    if fact.character_id is not None:
        return session.get_one(Character, fact.character_id).canonical_name
    if fact.place_id is not None:
        return session.get_one(Place, fact.place_id).canonical_name
    return "el mundo"


def load_vigente(session: Session, version_id: int, chapter: int) -> Vigente:
    names = session.query(Character.canonical_name).filter(Character.version_id == version_id)
    chapters = session.query(Chapter).filter(Chapter.version_id == version_id)
    known = {normalize_token(token) for c in chapters for token in tokenize(f"{c.title}\n{c.text}")}
    used = (
        session.query(Fact)
        .join(FactUsage, FactUsage.fact_id == Fact.id)
        .filter(
            Fact.version_id == version_id,
            Fact.attribute.in_(NOMINAL_ATTRIBUTES),
            FactUsage.chapter == chapter,
        )
        .order_by(Fact.id)
    )
    return Vigente(
        canonical_names=tuple(row[0] for row in names.order_by(Character.id)),
        known_words=frozenset(known),
        used_facts=tuple(UsedFact(_subject(session, f), f.attribute, f.value) for f in used),
    )


def missing_facts(text: str, vigente: Vigente) -> list[Diagnostic]:
    """El valor de un hecho nominal que el capítulo usaba y ya no aparece, con la coincidencia
    literal de 011 (019-C04)."""
    return [
        Diagnostic(
            "hecho",
            f"«{fact.value}» ({fact.attribute} de {fact.subject}) ya no aparece en el capítulo: "
            "si el cambio es intencionado, guardar cambiará la story bible",
            blocking=False,
            extra={"subject": fact.subject, "attribute": fact.attribute, "value": fact.value},
        )
        for fact in vigente.used_facts
        if not find_term_matches(text, fact.value)
    ]


def unknown_characters(text: str, vigente: Vigente) -> list[Diagnostic]:
    """Una palabra con mayúscula que no es de ningún nombre canónico, ni variante de uno, ni sale
    en ningún capítulo de la vigente: un aviso por palabra, en su primera aparición (019-C03)."""
    canonical_words = {w for name in vigente.canonical_names for w in letter_words(name)}
    seen: set[str] = set()
    found = []
    for match in _LETTERS.finditer(text):
        word = match.group(0)
        if not word[0].isupper() or word in canonical_words or word in seen:
            continue
        if normalize_token(word) in vigente.known_words:
            continue
        if name_variants("", word, vigente.canonical_names):
            continue
        seen.add(word)
        found.append(
            Diagnostic(
                "personaje_desconocido",
                f"«{word}» no es ningún personaje de la story bible",
                blocking=False,
                start=match.start(),
                end=match.end(),
                extra={"word": word},
            )
        )
    return found


def live_lint(
    session: Session, config: Config, novel: Novel, version_id: int, chapter: int, text: str
) -> list[Diagnostic]:
    """Solo lee: el mismo texto contra la misma vigente da los mismos diagnósticos."""
    vigente = load_vigente(session, version_id, chapter)
    timeline = load_timeline(session, version_id, chapter)
    return ordered(
        [
            *name_variant_diagnostics(text, vigente.canonical_names),
            *unknown_characters(text, vigente),
            *missing_facts(text, vigente),
            *banned_diagnostics(text, active_banned(session, novel.user_id, novel.id)),
            *prose_warnings(text, lint_inputs(session, version_id, config)),
            *reappearances(text, timeline),
            *wrong_ages(text, timeline, load_births(session, version_id)),
        ]
    )


def prose_warnings(text: str, inputs: LintInputs) -> list[Diagnostic]:
    """Los avisos de los cuatro linters de 018, con su métrica y su umbral (019-C06)."""
    return [
        Diagnostic(
            "linter",
            defect.message,
            blocking=False,
            extra={
                "linter": result.validator,
                "metric": result.metric,
                "threshold": threshold_comment(result, inputs),
            },
        )
        for result in lint_chapter(text, inputs)
        for defect in result.defects
    ]

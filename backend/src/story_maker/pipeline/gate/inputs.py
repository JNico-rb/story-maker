"""Lo que lee cada pasada del gate de la candidata tal como está: sus capítulos, los elementos
obligatorios con su asignación del outline y sus usos, las prohibidas activas al correr la pasada
y la ventana del juez (012-C3, C4, C5, C16; `architecture.md` §9.4).

Solo lecturas: ningún validador escribe aquí, y el veredicto lo calcula el código con campos
estructurados (012-I5)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

from sqlalchemy.orm import Session

from story_maker.domain.banned_terms import find_term_matches
from story_maker.domain.trope_catalog import TROPE_CATALOG
from story_maker.formal.defects import Defect
from story_maker.pipeline.planning.brief_view import BriefView, RecipientView
from story_maker.store.models import (
    BannedTerm,
    Brief,
    Chapter,
    Character,
    Fact,
    FactUsage,
    Novel,
    OutlineChapter,
)
from story_maker.store.story_bible import read_story_bible
from story_maker.validators.exact_names import EXACT_NAMES, name_variants
from story_maker.validators.judge import JudgeChapter, build_judge_window
from story_maker.validators.novel import (
    BannedTermMatch,
    ChapterText,
    MandatoryElement,
    NovelValidatorResult,
)


def chapters_of(session: Session, version_id: int) -> list[Chapter]:
    return list(
        session.query(Chapter)
        .filter(Chapter.version_id == version_id)
        .order_by(Chapter.number)
        .all()
    )


def mandatory_elements(
    session: Session, version_id: int
) -> tuple[tuple[MandatoryElement, ...], frozenset[str]]:
    """Cada elemento personal obligatorio de la candidata con los capítulos a los que el outline
    lo asignó, y los que tienen algún `UsoDeHecho` de alguno de sus hechos (012-C3)."""
    facts = (
        session.query(Fact)
        .filter(
            Fact.version_id == version_id,
            Fact.mandatory.is_(True),
            Fact.personal_element_id.is_not(None),
        )
        .order_by(Fact.id)
        .all()
    )
    outline = session.query(OutlineChapter).filter(OutlineChapter.version_id == version_id)
    assigned: dict[str, list[int]] = {}
    for chapter in outline.order_by(OutlineChapter.number):
        for element in cast(list[Any], chapter.assigned_elements):
            assigned.setdefault(str(element), []).append(chapter.number)
    used_facts = {
        row[0]
        for row in session.query(FactUsage.fact_id).filter(
            FactUsage.fact_id.in_([f.id for f in facts])
        )
    }
    labels: dict[str, str] = {}
    used: set[str] = set()
    for fact in facts:
        element = str(fact.personal_element_id)
        labels.setdefault(element, fact.value)
        if fact.id in used_facts:
            used.add(element)
    elements = tuple(
        MandatoryElement(element, label, tuple(assigned.get(element, ())))
        for element, label in labels.items()
    )
    return elements, frozenset(used)


def exact_names_result(chapters: Sequence[Chapter], names: Sequence[str]) -> NovelValidatorResult:
    """`nombres-exactos`, con la regla de 011, aplicado a cada capítulo (012-C4): un defecto
    bloqueante del capítulo por cada variante."""
    defects = tuple(
        Defect(EXACT_NAMES, None, True, chapter.number, variant.message)
        for chapter in chapters
        for variant in name_variants(chapter.title, chapter.text, names)
    )
    return NovelValidatorResult(EXACT_NAMES, not defects, defects)


def canonical_names(session: Session, version_id: int) -> tuple[str, ...]:
    rows = session.query(Character.canonical_name).filter(Character.version_id == version_id)
    return tuple(row[0] for row in rows.order_by(Character.id))


def chapter_texts(chapters: Sequence[Chapter]) -> tuple[ChapterText, ...]:
    return tuple(ChapterText(c.number, f"{c.title}\n{c.text}") for c in chapters)


def banned_matches(
    session: Session, user_id: int, novel_id: int, chapters: Sequence[ChapterText]
) -> tuple[BannedTermMatch, ...]:
    """Las coincidencias de las tres listas tal como están al correr la pasada (012-C5), con la
    coincidencia por tokens de 005."""
    entries = (
        session.query(BannedTerm)
        .filter(
            (BannedTerm.level == "global")
            | ((BannedTerm.level == "user") & (BannedTerm.user_id == user_id))
            | ((BannedTerm.level == "novel") & (BannedTerm.novel_id == novel_id))
        )
        .order_by(BannedTerm.id)
        .all()
    )
    return tuple(
        BannedTermMatch(entry.term, entry.level, variant, chapter.chapter)
        for chapter in chapters
        for entry in entries
        for needle in _needles(entry)
        for variant in find_term_matches(chapter.text, needle)
    )


def _needles(entry: BannedTerm) -> list[str]:
    if entry.type == "topic":
        return [str(k) for k in cast(list[Any], entry.keywords or [])]
    return [entry.term]


def judge_message(session: Session, version_id: int, novel_id: int) -> str:
    """La ventana del juez con la candidata tal como está (012-C16)."""
    novel = session.get_one(Novel, novel_id)
    brief = session.query(Brief).filter(Brief.novel_id == novel_id).one_or_none()
    chapters = tuple(
        JudgeChapter(c.number, c.title, c.text) for c in chapters_of(session, version_id)
    )
    return build_judge_window(
        novel.title or "",
        chapters,
        read_story_bible(session, version_id),
        TROPE_CATALOG,
        _brief_view(brief.content if brief is not None else {}),
    )


def _brief_view(content: Any) -> BriefView:
    """Del brief, el juez solo lee tono, género y deseos de trama (012-C16)."""
    data = content if isinstance(content, dict) else {}
    recipient = data.get("recipient") or {}
    return BriefView(
        recipient=RecipientView(name=str(recipient.get("name", "")), age=0),
        genre=str(data.get("genre", "")),
        tone=str(data.get("tone", "")),
        plot_wishes=tuple(str(w) for w in data.get("plot_wishes") or ()),
    )

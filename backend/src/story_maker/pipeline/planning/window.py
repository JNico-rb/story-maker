"""Ensambla la `VentanaDeContexto` del planner en modo `plan` (010-C06; `definitions.md` §4,
`architecture.md` §6.2).

Solo tres fuentes entran: el brief confirmado (`brief_view.BriefView`), la story bible inicial
(`story_bible_view.StoryBibleView`) y el `CatalogoDeTropos` como lista de evitación. Nunca el
texto libre, la cita de un `HechoExtraido`, una CanonCard recuperada o prosa de capítulo
(010-I1) — no hay parámetro por el que pudieran entrar."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from story_maker.domain.trope_catalog import Trope
from story_maker.pipeline.planning.brief_view import BriefView
from story_maker.pipeline.planning.story_bible_view import StoryBibleView
from story_maker.validators.outline import OutlineDefect


def build_planner_window(
    brief: BriefView,
    story_bible: StoryBibleView,
    catalog: tuple[Trope, ...],
    *,
    defects: tuple[OutlineDefect, ...] = (),
) -> str:
    """La ventana como JSON: es lo que lee el modelo en `SessionRequest.message` (003). Al
    replanificar, `defects` lleva los del intento anterior y nunca el plan que rechazó
    (010-C17): no hay ningún parámetro para pasarlo."""
    payload: dict[str, Any] = {
        "brief": _brief(brief, story_bible),
        "story_bible": _story_bible(story_bible),
        "trope_catalog": [asdict(trope) for trope in catalog],
    }
    if defects:
        payload["previous_defects"] = [d.message for d in defects]
    return json.dumps(payload, ensure_ascii=False, default=str)


def _brief(brief: BriefView, story_bible: StoryBibleView) -> dict[str, Any]:
    return {
        "recipient": {
            "name": brief.recipient.name,
            "age": brief.recipient.age,
            "traits": [asdict(t) for t in brief.recipient.traits],
        },
        "close_ones": [asdict(c) for c in brief.close_ones],
        "recollections": [asdict(r) for r in brief.recollections],
        "occasion": brief.occasion,
        "genre": brief.genre,
        "tone": brief.tone,
        "extension": brief.extension,
        "dedication": brief.dedication,
        "banned_novel": [asdict(b) for b in brief.banned_novel],
        "plot_wishes": list(brief.plot_wishes),
        "personal_elements": [
            {"label": e.label, "mandatory": e.mandatory} for e in story_bible.personal_elements
        ],
        "accepted_extracted_facts": [asdict(f) for f in brief.accepted_extracted_facts],
    }


def _story_bible(story_bible: StoryBibleView) -> dict[str, Any]:
    return {
        "present_year": story_bible.present_year,
        "characters": list(story_bible.character_names),
        "places": list(story_bible.place_names),
        "facts": [asdict(f) for f in story_bible.facts],
        "events": [asdict(e) for e in story_bible.events],
        "personal_elements": [asdict(e) for e in story_bible.personal_elements],
    }

"""Contradicción C6, por nivel, lugar y variante (008-C11)."""

from __future__ import annotations

import datetime as dt

from story_maker.domain.brief import (
    AcceptedFact,
    BannedEntry,
    BriefContent,
    CloseOne,
    PlotWish,
    Recipient,
    Recollection,
    Trait,
    all_contradictions,
)

CREATED_AT = dt.date(2026, 9, 24)


def _rules(
    content: BriefContent,
    banned: list[BannedEntry],
    facts: list[AcceptedFact] | None = None,
) -> list[str]:
    return [c.rule for c in all_contradictions(content, CREATED_AT, banned, facts or [])]


def test_a_banned_name_on_the_always_mandatory_recipient_name_is_c6() -> None:
    content = BriefContent(recipient=Recipient(name="Marta", age=40))
    banned = [BannedEntry(term="marta", type="word", level="novel")]

    assert "C6" in _rules(content, banned)


def test_a_mandatory_close_one_with_a_banned_name_is_c6() -> None:
    content = BriefContent(
        close_ones=[CloseOne(name="Toby", relation="mascota", species="animal", mandatory=True)]
    )
    banned = [BannedEntry(term="Toby", type="word", level="user")]

    assert "C6" in _rules(content, banned)


def test_a_non_mandatory_close_one_elsewhere_unmatched_is_not_c6() -> None:
    content = BriefContent(
        close_ones=[CloseOne(name="Toby", relation="mascota", species="animal", mandatory=False)]
    )
    banned = [BannedEntry(term="Toby", type="word", level="user")]

    assert "C6" not in _rules(content, banned)


def test_the_dedication_is_always_checked() -> None:
    content = BriefContent(dedication="Para Marta, lejos de camino")
    banned = [BannedEntry(term="camino", type="word", level="user")]

    assert "C6" in _rules(content, banned)


def test_a_plural_variant_in_the_dedication_matches_the_singular_term() -> None:
    content = BriefContent(dedication="Para Marta, muchos caminos")
    banned = [BannedEntry(term="camino", type="word", level="novel")]

    assert "C6" in _rules(content, banned)


def test_an_accent_variant_on_a_mandatory_recollection_matches() -> None:
    content = BriefContent(
        recollections=[Recollection(statement="la féria del pueblo", place="p", mandatory=True)]
    )
    banned = [BannedEntry(term="feria", type="word", level="novel")]

    assert "C6" in _rules(content, banned)


def test_the_same_recollection_not_mandatory_does_not_match() -> None:
    content = BriefContent(
        recollections=[Recollection(statement="la féria del pueblo", place="p", mandatory=False)]
    )
    banned = [BannedEntry(term="feria", type="word", level="novel")]

    assert "C6" not in _rules(content, banned)


def test_a_topic_matches_by_any_of_its_keywords_in_a_plot_wish() -> None:
    content = BriefContent(plot_wishes=[PlotWish(statement="que salga un androide")])
    banned = [
        BannedEntry(term="robots", type="topic", level="novel", keywords=["robot", "androide"])
    ]

    assert "C6" in _rules(content, banned)


def test_ex_does_not_match_examen_word_boundary() -> None:
    content = BriefContent(
        recollections=[Recollection(statement="hizo un examen difícil", place="p", mandatory=True)]
    )
    banned = [BannedEntry(term="ex", type="word", level="novel")]

    assert "C6" not in _rules(content, banned)


def test_a_global_level_term_on_a_mandatory_trait_matches() -> None:
    content = BriefContent(recipient=Recipient(traits=[Trait(statement="idiota", mandatory=True)]))
    banned = [BannedEntry(term="idiota", type="word", level="global")]

    assert "C6" in _rules(content, banned)


def test_a_user_level_term_on_an_accepted_and_mandatory_fact_matches() -> None:
    content = BriefContent()
    banned = [BannedEntry(term="Sopelana", type="word", level="user")]
    facts = [AcceptedFact(id=1, subject="Marta", value="Vive en Sopelana", mandatory=True)]

    assert "C6" in _rules(content, banned, facts)


def test_the_same_fact_accepted_but_not_mandatory_does_not_match() -> None:
    content = BriefContent()
    banned = [BannedEntry(term="Sopelana", type="word", level="user")]
    facts = [AcceptedFact(id=1, subject="Marta", value="Vive en Sopelana", mandatory=False)]

    assert "C6" not in _rules(content, banned, facts)

"""Comprobación de schema: forma y referencias internas (008-C13)."""

from __future__ import annotations

from story_maker.domain.brief import (
    AcceptedFact,
    BriefContent,
    CloseOne,
    Recipient,
    Recollection,
    schema_errors,
)


def _messages(content: BriefContent, facts: list[AcceptedFact] | None = None) -> list[str]:
    return [e.message for e in schema_errors(content, facts or [])]


def test_an_unknown_present_in_a_recollection_is_flagged() -> None:
    content = BriefContent(
        recollections=[Recollection(statement="x", age=8, place="p", present=["Luis"])]
    )

    assert "Presente desconocido en el recuerdo" in _messages(content)


def test_a_valid_close_one_as_excluded_is_not_flagged() -> None:
    content = BriefContent(
        close_ones=[CloseOne(name="Toby", relation="mascota", species="animal")],
        recollections=[Recollection(statement="x", age=8, place="p", excluded="Toby")],
    )

    assert _messages(content) == []


def test_the_recipient_or_an_unknown_name_as_excluded_is_invalid() -> None:
    content = BriefContent(
        recipient=Recipient(name="Marta"),
        recollections=[Recollection(statement="x", age=8, place="p", excluded="Marta")],
    )

    assert "Excluido no válido" in _messages(content)


def test_a_recollection_with_both_age_and_year_needs_exactly_one() -> None:
    content = BriefContent(recollections=[Recollection(statement="x", age=8, year=2020, place="p")])

    assert "El recuerdo necesita edad o año, uno solo" in _messages(content)


def test_a_recollection_with_neither_age_nor_year_needs_exactly_one() -> None:
    content = BriefContent(recollections=[Recollection(statement="x", place="p")])

    assert "El recuerdo necesita edad o año, uno solo" in _messages(content)


def test_a_recollection_without_a_place_is_flagged() -> None:
    content = BriefContent(recollections=[Recollection(statement="x", age=8, place="")])

    assert "Recuerdo sin lugar" in _messages(content)


def test_a_close_one_without_relation_or_species_is_incomplete() -> None:
    without_relation = BriefContent(close_ones=[CloseOne(name="Toby", species="animal")])
    without_species = BriefContent(close_ones=[CloseOne(name="Toby", relation="mascota")])

    assert "Allegado incompleto" in _messages(without_relation)
    assert "Allegado incompleto" in _messages(without_species)


def test_two_close_ones_with_the_same_name_is_a_repeated_name() -> None:
    content = BriefContent(
        close_ones=[
            CloseOne(name="Luis", relation="amigo", species="person"),
            CloseOne(name="Luis", relation="primo", species="person"),
        ]
    )

    assert "Nombre repetido" in _messages(content)


def test_a_close_one_named_like_the_recipient_is_a_repeated_name() -> None:
    content = BriefContent(
        recipient=Recipient(name="Marta"),
        close_ones=[CloseOne(name="Marta", relation="amiga", species="person")],
    )

    assert "Nombre repetido" in _messages(content)


def test_an_accepted_fact_whose_subject_is_no_longer_in_the_brief_is_unknown() -> None:
    content = BriefContent(
        recipient=Recipient(name="Marta"),
        close_ones=[CloseOne(name="Luisa", relation="amiga", species="person")],
    )
    facts = [AcceptedFact(id=1, subject="Luis", value="algo", mandatory=False)]

    assert "Sujeto desconocido" in _messages(content, facts)


def test_the_unknown_subject_disappears_once_the_close_one_is_renamed_back() -> None:
    content = BriefContent(
        recipient=Recipient(name="Marta"),
        close_ones=[CloseOne(name="Luis", relation="amigo", species="person")],
    )
    facts = [AcceptedFact(id=1, subject="Luis", value="algo", mandatory=False)]

    assert "Sujeto desconocido" not in _messages(content, facts)
